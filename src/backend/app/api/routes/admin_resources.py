from urllib.parse import urlsplit
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, func, or_, DateTime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.backend.app.api.admin_auth import require_admin
from src.backend.app.database.models.admin_resource_audit import AdminResourceAudit
from src.backend.app.database.models.competency_resource_link import CompetencyResourceLink
from src.backend.app.database.models.learning_resource import LearningResource
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
from src.backend.app.services.admin_mfa_verification import verify_and_consume_admin_totp
from src.backend.app.services.career_competency_profiles import CAREER_COMPETENCY_PROFILES
from datetime import datetime, timezone
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.learning_resource_skill import LearningResourceSkill



router = APIRouter(
    prefix="/admin/resources",
    tags=["Administration"],
)


class CompetencyAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    career_key: str = Field(min_length=1, max_length=120)
    competency_key: str = Field(min_length=1, max_length=120)


class CreateResourceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    provider: str | None = Field(default=None, max_length=150)
    resource_type: str = Field(min_length=1, max_length=50)
    url: str = Field(min_length=10, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    assignments: list[CompetencyAssignment] = Field(
        default_factory=list,
        max_length=50,
    )
    skill_ids: list[int] = Field(default_factory=list, max_length=50)
    totp_code: str = Field(pattern=r"^[0-9]{6}$")

    @field_validator("title", "resource_type")
    @classmethod
    def validate_nonempty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be empty.")
        return value

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()

        try:
            parsed = urlsplit(value)
            valid = (
                parsed.scheme == "https"
                and bool(parsed.hostname)
                and parsed.username is None
                and parsed.password is None
                and not any(char.isspace() for char in value)
            )
        except ValueError:
            valid = False

        if not valid:
            raise ValueError("A valid HTTPS resource URL is required.")

        return value


class UpdateResourceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=255)
    provider: str | None = Field(default=None, max_length=150)
    resource_type: str | None = Field(default=None, min_length=1, max_length=50)
    url: str | None = Field(default=None, min_length=10, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    totp_code: str = Field(pattern=r"^[0-9]{6}$")
    skill_ids: list[int] | None = Field(default=None, max_length=50)
    assignments: list[CompetencyAssignment] | None = Field(
        default=None, max_length=50
    )


    @field_validator("title", "resource_type")
    @classmethod
    def validate_required_text(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("Value cannot be empty.")
        return value.strip()

    @field_validator("url")
    @classmethod
    def validate_resource_url(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("URL cannot be empty.")

        value = value.strip()
        try:
            parsed = urlsplit(value)
            valid = (
                parsed.scheme == "https"
                and bool(parsed.hostname)
                and parsed.username is None
                and parsed.password is None
                and not any(char.isspace() for char in value)
            )
        except ValueError:
            valid = False

        if not valid:
            raise ValueError("A valid HTTPS URL is required.")

        return value


class ReplaceAssignmentsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assignments: list[CompetencyAssignment] = Field(max_length=50)
    totp_code: str = Field(pattern=r"^[0-9]{6}$")

class ResourceArchiveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    totp_code: str = Field(pattern=r"^[0-9]{6}$")

def validate_assignments(
    assignments: list[CompetencyAssignment],
) -> list[tuple[str, str]]:
    validated = set()

    for assignment in assignments:
        career_key = assignment.career_key.strip()
        competency_key = assignment.competency_key.strip()

        profile = CAREER_COMPETENCY_PROFILES.get(career_key)

        if not profile or not any(
            item["key"] == competency_key
            for item in profile
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Unknown career/competency assignment: "
                    f"{career_key}/{competency_key}"
                ),
            )

        key = (career_key, competency_key)

        if key in validated:
            raise HTTPException(
                status_code=422,
                detail="Duplicate competency assignment.",
            )

        validated.add(key)

    return sorted(validated)


@router.get("")
def list_learning_resources(
    q: str = Query(default="", max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    include_archived: bool = Query(default=False),
):
    query = select(LearningResource)
    count_query = select(func.count()).select_from(LearningResource)
    if not include_archived:
        query = query.where(LearningResource.archived_at.is_(None))
        count_query = count_query.where(
            LearningResource.archived_at.is_(None)
        )

    if q.strip():
        search = f"%{q.strip()}%"
        condition = or_(
            LearningResource.title.ilike(search),
            LearningResource.provider.ilike(search),
            LearningResource.url.ilike(search),
        )

        query = query.where(condition)
        count_query = count_query.where(condition)

    total = db.scalar(count_query) or 0

    resources = db.scalars(
        query
        .order_by(LearningResource.title, LearningResource.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    resource_ids = [resource.id for resource in resources]
    skills_by_resource = {
        resource_id: [] for resource_id in resource_ids
    }

    if resource_ids:
        skill_rows = db.execute(
            select(
                LearningResourceSkill.learning_resource_id,
                Skill.id,
                Skill.name,
            )
            .join(
                Skill,
                Skill.id == LearningResourceSkill.skill_id,
            )
            .where(
                LearningResourceSkill.learning_resource_id.in_(
                    resource_ids
                )
            )
            .order_by(Skill.name)
        ).all()

        for resource_id, skill_id, skill_name in skill_rows:
            skills_by_resource[resource_id].append({
                "id": skill_id,
                "name": skill_name,
            })

    assignments_by_id = {resource_id: [] for resource_id in resource_ids}

    if resource_ids:
        links = db.scalars(
            select(CompetencyResourceLink)
            .where(
                CompetencyResourceLink.resource_id.in_(resource_ids)
            )
            .order_by(
                CompetencyResourceLink.career_key,
                CompetencyResourceLink.competency_key,
            )
        ).all()

        for link in links:
            assignments_by_id[link.resource_id].append({
                "career_key": link.career_key,
                "competency_key": link.competency_key,
            })

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "resources": [
            {
                "id": resource.id,
                "title": resource.title,
                "provider": resource.provider,
                "resource_type": resource.resource_type,
                "url": resource.url,
                "description": resource.description,
                "assignments": assignments_by_id[resource.id],
                "skills": skills_by_resource[resource.id],
                "archived_at": resource.archived_at,
            }
            for resource in resources
        ],
    }


@router.get("/skills")
def list_resource_skills(
    q: str = Query(default="", max_length=100),
    limit: int = Query(default=30, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    search = q.strip()

    query = select(Skill)

    if search:
        query = query.where(Skill.name.ilike(f"%{search}%"))

    skills = db.scalars(
        query.order_by(Skill.name, Skill.id).limit(limit)
    ).all()

    return {
        "skills": [
            {
                "id": skill.id,
                "name": skill.name,
                "category": skill.category,
            }
            for skill in skills
        ]
    }

@router.patch("/{resource_id}")
def update_learning_resource(
    resource_id: int,
    payload: UpdateResourceRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    changes = payload.model_dump(
        exclude_unset=True,
        exclude={"totp_code", "skill_ids", "assignments"},
    )
    replace_skills = payload.skill_ids is not None
    replace_assignments = payload.assignments is not None

    if not changes and not replace_skills and not replace_assignments:
        raise HTTPException(422, "No resource changes provided.")

    requested_skills = set(payload.skill_ids or [])
    if replace_skills:
        if len(requested_skills) != len(payload.skill_ids) or any(
            skill_id <= 0 for skill_id in requested_skills
        ):
            raise HTTPException(422, "Invalid or duplicate skill IDs.")

        found = set(db.scalars(
            select(Skill.id).where(Skill.id.in_(requested_skills))
        ).all())

        if found != requested_skills:
            raise HTTPException(
                422, "One or more selected skills do not exist."
            )

    requested_assignments = (
        set(validate_assignments(payload.assignments))
        if replace_assignments else set()
    )

    resource = db.get(LearningResource, resource_id)
    if resource is None:
        raise HTTPException(404, "Learning resource not found.")
    if resource.archived_at is not None:
        raise HTTPException(
            409, "Restore this resource before editing it."
        )

    current_skills = set(db.scalars(
        select(LearningResourceSkill.skill_id).where(
            LearningResourceSkill.learning_resource_id == resource_id
        )
    ).all())
    current_assignments = set(db.execute(
        select(
            CompetencyResourceLink.career_key,
            CompetencyResourceLink.competency_key,
        ).where(CompetencyResourceLink.resource_id == resource_id)
    ).all())

    if not (
        (requested_skills if replace_skills else current_skills)
        or (requested_assignments if replace_assignments else current_assignments)
    ):
        raise HTTPException(
            422, "Choose at least one skill or career competency."
        )

    verify_and_consume_admin_totp(
        db=db,
        user_id=admin.id,
        code=payload.totp_code,
    )

    resource = db.scalar(
        select(LearningResource)
        .where(LearningResource.id == resource_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    if resource is None:
        raise HTTPException(404, "Learning resource no longer exists.")
    if resource.archived_at is not None:
        raise HTTPException(
            409, "Restore this resource before editing it."
        )

    skill_links = db.scalars(
        select(LearningResourceSkill).where(
            LearningResourceSkill.learning_resource_id == resource_id
        )
    ).all()
    assignment_links = db.scalars(
        select(CompetencyResourceLink).where(
            CompetencyResourceLink.resource_id == resource_id
        )
    ).all()

    old_skills = {link.skill_id for link in skill_links}
    old_assignments = {
        (link.career_key, link.competency_key)
        for link in assignment_links
    }
    new_skills = requested_skills if replace_skills else old_skills
    new_assignments = (
        requested_assignments if replace_assignments else old_assignments
    )

    if not new_skills and not new_assignments:
        raise HTTPException(
            422, "Choose at least one skill or career competency."
        )

    before = {
        "fields": {key: getattr(resource, key) for key in changes},
        "skill_ids": sorted(old_skills),
        "assignments": [list(item) for item in sorted(old_assignments)],
    }

    for key, value in changes.items():
        if key in {"provider", "description"}:
            value = value.strip() or None if value else None
        setattr(resource, key, value)

    if replace_skills:
        for link in skill_links:
            if link.skill_id not in new_skills:
                db.delete(link)

        for skill_id in new_skills - old_skills:
            db.add(LearningResourceSkill(
                learning_resource_id=resource_id,
                skill_id=skill_id,
            ))

    if replace_assignments:
        for link in assignment_links:
            if (link.career_key, link.competency_key) not in new_assignments:
                db.delete(link)

        for career_key, competency_key in new_assignments - old_assignments:
            db.add(CompetencyResourceLink(
                resource_id=resource_id,
                career_key=career_key,
                competency_key=competency_key,
            ))

    after = {
        "fields": {key: getattr(resource, key) for key in changes},
        "skill_ids": sorted(new_skills),
        "assignments": [list(item) for item in sorted(new_assignments)],
    }

    db.add(AdminResourceAudit(
        actor_user_id=admin.id,
        resource_id=resource_id,
        action="resource_updated",
        details={"before": before, "after": after},
    ))

    try:
        db.commit()
        db.refresh(resource)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            409, "Resource update conflicts with existing data."
        ) from exc

    return {
        "id": resource.id,
        "title": resource.title,
        "provider": resource.provider,
        "resource_type": resource.resource_type,
        "url": resource.url,
        "description": resource.description,
        "skill_ids": sorted(new_skills),
        "assignments": [
            {"career_key": career_key, "competency_key": competency_key}
            for career_key, competency_key in sorted(new_assignments)
        ],
    }


@router.put("/{resource_id}/assignments")
def replace_resource_assignments(
    resource_id: int,
    payload: ReplaceAssignmentsRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    requested = set(validate_assignments(payload.assignments))

    if db.get(LearningResource, resource_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Learning resource not found.",
        )

    verify_and_consume_admin_totp(
        db=db,
        user_id=admin.id,
        code=payload.totp_code,
    )

    resource = db.scalar(
        select(LearningResource)
        .where(LearningResource.id == resource_id)
        .with_for_update()
    )

    if resource is None:
        raise HTTPException(
            status_code=404,
            detail="Learning resource no longer exists.",
        )
    if resource.archived_at is not None:
        raise HTTPException(
            409, "Restore this resource before modifying assignments."
        )


    links = db.scalars(
        select(CompetencyResourceLink).where(
            CompetencyResourceLink.resource_id == resource_id
        )
    ).all()

    existing = {
        (link.career_key, link.competency_key)
        for link in links
    }

    for link in links:
        if (link.career_key, link.competency_key) not in requested:
            db.delete(link)

    for career_key, competency_key in requested - existing:
        db.add(
            CompetencyResourceLink(
                resource_id=resource_id,
                career_key=career_key,
                competency_key=competency_key,
            )
        )

    db.add(
        AdminResourceAudit(
            actor_user_id=admin.id,
            resource_id=resource_id,
            action="resource_assignments_updated",
            details={
                "before": [list(item) for item in sorted(existing)],
                "after": [list(item) for item in sorted(requested)],
            },
        )
    )

    db.commit()

    return {
        "resource_id": resource_id,
        "assignments": [
            {
                "career_key": career_key,
                "competency_key": competency_key,
            }
            for career_key, competency_key in sorted(requested)
        ],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_learning_resource(
    payload: CreateResourceRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    assignments = validate_assignments(payload.assignments)
    skill_ids = payload.skill_ids

    if len(skill_ids) != len(set(skill_ids)) or any(
    skill_id <= 0 for skill_id in skill_ids
    ):
        raise HTTPException(
            status_code=422,
            detail="Invalid or duplicate skill IDs.",
        )

    if not skill_ids and not assignments:
        raise HTTPException(
            status_code=422,
            detail="Choose at least one skill or career competency.",
        )

    skills = db.scalars(
        select(Skill).where(Skill.id.in_(skill_ids))
    ).all() if skill_ids else []

    if {skill.id for skill in skills} != set(skill_ids):
        raise HTTPException(
            status_code=422,
            detail="One or more selected skills do not exist.",
        )


    existing = db.scalar(
        select(LearningResource.id).where(
            LearningResource.url == payload.url
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="A learning resource with this URL already exists.",
        )

    # The verifier consumes the TOTP step and commits it before
    # any resource mutation is attempted.
    verify_and_consume_admin_totp(
        db=db,
        user_id=admin.id,
        code=payload.totp_code,
    )

    resource = LearningResource(
        title=payload.title,
        provider=(payload.provider or "").strip() or None,
        resource_type=payload.resource_type,
        url=payload.url,
        description=(payload.description or "").strip() or None,
    )

    try:
        db.add(resource)
        db.flush()

        for career_key, competency_key in assignments:
            db.add(
                CompetencyResourceLink(
                    career_key=career_key,
                    competency_key=competency_key,
                    resource_id=resource.id,
                )
            )
        for skill_id in skill_ids:
            db.add(
                LearningResourceSkill(
                    learning_resource_id=resource.id,
                    skill_id=skill_id,
                )
            )

        db.add(
            AdminResourceAudit(
                actor_user_id=admin.id,
                resource_id=resource.id,
                action="resource_created",
                details={
                    "title": resource.title,
                    "url": resource.url,
                    "skill_ids": skill_ids,
                    "skill_names": sorted(skill.name for skill in skills),
                    "assignments": [
                        {
                            "career_key": career_key,
                            "competency_key": competency_key,
                        }
                        for career_key, competency_key in assignments
                    ],
                },
            )
        )

        db.commit()
        db.refresh(resource)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="The resource or one of its assignments conflicts with existing data.",
        ) from exc

    return {
        "id": resource.id,
        "title": resource.title,
        "provider": resource.provider,
        "resource_type": resource.resource_type,
        "url": resource.url,
        "description": resource.description,
        "skill_ids": skill_ids,
        "assignments": [
            {
                "career_key": career_key,
                "competency_key": competency_key,
            }
            for career_key, competency_key in assignments
        ],
    }


@router.delete("/{resource_id}")
def archive_learning_resource(
    resource_id: int,
    payload: ResourceArchiveRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    resource = db.get(LearningResource, resource_id)

    if resource is None:
        raise HTTPException(404, "Learning resource not found.")

    if resource.archived_at is not None:
        raise HTTPException(409, "Resource is already archived.")

    verify_and_consume_admin_totp(
        db=db,
        user_id=admin.id,
        code=payload.totp_code,
    )

    resource = db.scalar(
        select(LearningResource)
        .where(LearningResource.id == resource_id)
        .with_for_update()
    )

    if resource is None:
        raise HTTPException(404, "Learning resource not found.")

    if resource.archived_at is not None:
        raise HTTPException(409, "Resource is already archived.")

    resource.archived_at = datetime.now(timezone.utc)

    db.add(
        AdminResourceAudit(
            actor_user_id=admin.id,
            resource_id=resource.id,
            action="resource_archived",
            details={
                "title": resource.title,
                "url": resource.url,
                "archived_at": resource.archived_at.isoformat(),
            },
        )
    )

    db.commit()

    return {
        "id": resource_id,
        "message": "Learning resource archived.",
    }

@router.post("/{resource_id}/restore")
def restore_learning_resource(
    resource_id: int,
    payload: ResourceArchiveRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    resource = db.get(LearningResource, resource_id)

    if resource is None:
        raise HTTPException(404, "Learning resource not found.")

    if resource.archived_at is None:
        raise HTTPException(409, "Resource is already active.")

    verify_and_consume_admin_totp(
        db=db,
        user_id=admin.id,
        code=payload.totp_code,
    )

    resource = db.scalar(
        select(LearningResource)
        .where(LearningResource.id == resource_id)
        .with_for_update()
    )

    if resource is None:
        raise HTTPException(404, "Learning resource not found.")

    if resource.archived_at is None:
        raise HTTPException(409, "Resource is already active.")

    previous_archived_at = resource.archived_at.isoformat()
    resource.archived_at = None

    db.add(
        AdminResourceAudit(
            actor_user_id=admin.id,
            resource_id=resource.id,
            action="resource_restored",
            details={
                "title": resource.title,
                "url": resource.url,
                "previous_archived_at": previous_archived_at,
            },
        )
    )

    db.commit()

    return {
        "id": resource_id,
        "message": "Learning resource restored.",
    }

@router.get("/options")
def get_resource_assignment_options(
    admin: User = Depends(require_admin),
):
    return {
        "careers": [
            {
                "key": career_key,
                "name": career_key.replace("_", " ").title(),
                "competencies": [
                    {
                        "key": item["key"],
                        "name": item["name"],
                    }
                    for item in profile
                ],
            }
            for career_key, profile in sorted(
                CAREER_COMPETENCY_PROFILES.items()
            )
        ]
    }