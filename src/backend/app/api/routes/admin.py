from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import func, select, text, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json
from pathlib import Path
from datetime import datetime, timezone
from time import perf_counter
from src.backend.app.services.career_competency_profiles import (CAREER_COMPETENCY_PROFILES)
from src.backend.app.api.admin_auth import require_admin
from src.backend.app.core.admin_logging import (read_system_events, record_system_event)
from src.backend.app.database.models.user import User
from src.backend.app.database.models.career import Career
from src.backend.app.database.models.user_skill import UserSkill
from src.backend.app.database.models.user_competency_assessment import ( UserCompetencyAssessment)
from src.backend.app.database.session import get_db
from src.backend.app.core.admin_logging import LOG_DIR, LOG_FILE
from src.backend.app.services.llm_health_service import (check_llm_health)
from src.backend.app.services.recommendation_health_service import ( check_recommendation_model_health)
from src.backend.app.database.models.competency_resource_link import (CompetencyResourceLink)
from src.backend.app.database.models.learning_resource import (LearningResource)
from src.backend.app.services.learning_resource_service import get_resources_for_skills



router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
    dependencies=[Depends(require_admin)],
)


@router.get("/me")
def get_admin_identity(
    admin: User = Depends(require_admin),
):
    return {
        "id": admin.id,
        "full_name": admin.full_name,
        "role": admin.role,
    }


@router.get("/overview")
def get_admin_overview(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total_users = db.scalar(
        select(func.count(User.id))
    ) or 0

    total_admins = db.scalar(
        select(func.count(User.id)).where(
            User.role == "admin"
        )
    ) or 0

    completed_onboarding = db.scalar(
        select(func.count(User.id)).where(
            User.onboarding_completed.is_(True)
        )
    ) or 0

    total_careers = db.scalar(
        select(func.count(Career.id))
    ) or 0

    total_user_skills = db.scalar(
        select(func.count()).select_from(UserSkill)
    ) or 0

    total_assessments = db.scalar(
        select(func.count()).select_from(
            UserCompetencyAssessment
        )
    ) or 0

    record_system_event(
        "admin",
        "overview_viewed",
        actor_user_id=admin.id,
    )

    return {
        "users": {
            "total": total_users,
            "administrators": total_admins,
            "onboarding_completed": completed_onboarding,
        },
        "careers": {
            "total": total_careers,
        },
        "activity": {
            "recorded_user_skills": total_user_skills,
            "competency_assessments": total_assessments,
        },
    }


@router.get("/users")
def list_admin_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total = db.scalar(
        select(func.count(User.id))
    ) or 0

    users = db.scalars(
        select(User)
        .order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    record_system_event(
        "admin",
        "user_directory_viewed",
        actor_user_id=admin.id,
    )

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "users": [
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "onboarding_completed": user.onboarding_completed,
                "created_at": user.created_at,
                "suspended_at": user.suspended_at,
                "suspension_reason": user.suspension_reason,
            }
            for user in users
        ],
    }


@router.get("/logs")
def list_admin_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    admin: User = Depends(require_admin),
):
    record_system_event(
        "admin",
        "system_logs_viewed",
        actor_user_id=admin.id,
    )

    return read_system_events(
        page=page,
        page_size=page_size,
        severity=severity,
        category=category,
    )


@router.get("/careers/{career_key}/resources")
def get_admin_career_resources(
    career_key: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    profile = CAREER_COMPETENCY_PROFILES.get(career_key)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Career profile not found.",
        )

    rows = db.execute(
        select(
            CompetencyResourceLink.competency_key,
            LearningResource,
        )
        .join(
            LearningResource,
            LearningResource.id
            == CompetencyResourceLink.resource_id,
        )
        .where(
            CompetencyResourceLink.career_key == career_key,
            LearningResource.archived_at.is_(None),
        )
        .order_by(
            CompetencyResourceLink.competency_key,
            LearningResource.title,
            LearningResource.id,
        )
    ).all()

    mapping_index = {}

    for competency_key, resource in rows:
        mapping_index.setdefault(
            competency_key, []
        ).append({
            "id": resource.id,
            "title": resource.title,
            "provider": resource.provider,
            "resource_type": resource.resource_type,
            "url": resource.url,
            "description": resource.description,
        })

    competencies = []
    covered_count = 0
    unique_resource_ids = set()
    skill_names = sorted({
        name
        for group in profile
        for name in (group.get("any_of") or [])
    })

    global_resources = get_resources_for_skills(db, skill_names)

    for group in profile:
        competency_key = group["key"]
        resources = list(mapping_index.get(competency_key, []))
        existing_ids = {resource["id"] for resource in resources}
        competency_skills = set(group.get("any_of") or [])

        for resource in global_resources:
            if resource["id"] in existing_ids:
                continue

            if not competency_skills.intersection(
                resource["matched_skills"]
            ):
                continue

            resources.append({
                "id": resource["id"],
                "title": resource["title"],
                "provider": resource["provider"],
                "resource_type": resource["resource_type"],
                "url": resource["url"],
                "description": resource["description"],
            })

            existing_ids.add(resource["id"])


        resources.sort(
            key=lambda item: (
                (item["provider"] or "").lower(),
                item["title"].lower(),
            )
        )

        if resources:
            covered_count += 1

        unique_resource_ids.update(
            resource["id"] for resource in resources
        )

        competencies.append({
            "key": competency_key,
            "name": group["name"],
            "level": group["level"],
            "resources": resources,
        })

    return {
        "career_key": career_key,
        "competency_count": len(competencies),
        "covered_competencies": covered_count,
        "unique_resources": len(unique_resource_ids),
        "competencies": competencies,
    }


@router.get("/health")
def get_admin_system_health(
    db: Session = Depends(get_db),
):
    """
    Check selected CareerForge services.

    The endpoint is protected by the existing
    administrator dependency on the router.
    """

    checks = {}

    # 1. Database connectivity
    started = perf_counter()

    try:
        db.execute(text("SELECT 1")).scalar_one()

        checks["database"] = {
            "status": "healthy",
            "message": "PostgreSQL query succeeded.",
            "latency_ms": round(
                (perf_counter() - started) * 1000,
                2,
            ),
        }

    except Exception:
        checks["database"] = {
            "status": "unhealthy",
            "message": "Database health query failed.",
            "latency_ms": None,
        }

        db.rollback()

    # 2. Learning-resource catalog
    try:
        resource_count = db.scalar(
            select(func.count()).select_from(LearningResource)
        ) or 0
        mapping_count = db.scalar(
            select(func.count()).select_from(CompetencyResourceLink)
        ) or 0
        healthy = resource_count > 0 and mapping_count > 0
        checks["resource_catalog"] = {
            "status": "healthy" if healthy else "unhealthy",
            "message": (
                "PostgreSQL resource catalog available."
                if healthy
                else "Resource catalog is empty or incomplete."
            ),
            "resources": resource_count,
            "mappings": mapping_count,
        }
    except SQLAlchemyError:
        db.rollback()
        checks["resource_catalog"] = {
            "status": "unhealthy",
            "message": "Could not query the resource catalog.",
        }
    # 3. System logging
    try:
        import tempfile

        LOG_DIR.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryFile(dir=LOG_DIR):
            pass

        checks["logging"] = {
            "status": "healthy",
            "message": (
                "Log directory is writable."
                if LOG_FILE.exists()
                else "Log directory is writable; no active log file yet."
            ),
        }
    except OSError:
        checks["logging"] = {
            "status": "unhealthy",
            "message": "Logging directory is not writable.",
        }

    # 4. Recommendation model
    checks["recommendation_model"] = (
        check_recommendation_model_health()
    )

    # 5. AI mentor
    checks["ai_mentor"] = check_llm_health()

    measured = [
        check
        for check in checks.values()
        if check["status"] != "not_checked"
    ]

    healthy = all(
        check["status"] == "healthy"
        for check in measured
    )

    return {
        "status": "healthy" if healthy else "degraded",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }