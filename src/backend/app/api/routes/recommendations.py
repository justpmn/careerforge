from fastapi import (APIRouter,HTTPException, File, Form, UploadFile, Depends)
from src.backend.app.services.resume_text_extractor import (extract_resume_text,)
from src.backend.app.schemas.recommendation import (RecommendationRequest,RecommendationResponse)
from sqlalchemy.orm import Session
from src.backend.app.database.session import (get_db)
from src.backend.app.services.resume_persistence_service import (save_resume_analysis)
from src.backend.app.services.recommendation_service import (analyze_career_text, analyze_personalized_career_text, get_recommendation_service)
from sqlalchemy import select
from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.models.resume import Resume
from src.backend.app.services.career_preference_service import personalize_recommendations
from src.backend.app.services.core_skill_coverage_service import (get_user_core_skill_coverage)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)

class SavedResumeAnalysis(RecommendationResponse):
    filename: str
    
@router.post(
    "/analyze",
    response_model=RecommendationResponse,
)
def analyze_recommendation(
    request: RecommendationRequest,
):
    try:
        return analyze_career_text(
            text=request.text,
            top_k=request.top_k,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

MAX_RESUME_SIZE = 5 * 1024 * 1024


@router.post(
    "/upload",
    response_model=RecommendationResponse,
)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    top_k: int = Form(default=3),
    db: Session = Depends(get_db),
    authenticated_user_id: int = Depends(get_current_user_id),
):
    if top_k < 1 or top_k > 5:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 5.",
        )
    if user_id != authenticated_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot upload a CV for another user.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_RESUME_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Resume file must not exceed 5 MB.",
        )

    try:
        text = extract_resume_text(
            filename=file.filename or "",
            file_bytes=file_bytes,
        )

        result = analyze_personalized_career_text(
            db=db,
            user_id=user_id,
            text=text,
            top_k=top_k,
        )

        save_resume_analysis(
            db=db,
            user_id=authenticated_user_id,
            filename=file.filename or "",
            extracted_text=text,
            extracted_skills=result["extracted_skills"],
            model_skills=result["model_skills"],
            ignored_skills=result["ignored_skills"],
            recommendations=result["recommendations"],
            model_recommendations=result["model_recommendations"],
        )

        return result

    except ValueError as error:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception:
        db.rollback()
        raise

    finally:
        await file.close()
        

@router.get(
    "/resumes/latest",
    response_model=SavedResumeAnalysis | None,
)
def get_latest_resume_analysis(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    resume = db.scalar(
        select(Resume)
        .where(
            Resume.user_id == user_id,
            Resume.analysis_result.is_not(None),
        )
        .order_by(Resume.id.desc())
        .limit(1)
    )

    if resume is None:
        return None

    return SavedResumeAnalysis(
        filename=resume.file_name,
        **resume.analysis_result,
    )
