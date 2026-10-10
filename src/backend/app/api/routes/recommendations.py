from fastapi import (APIRouter,HTTPException, File, Form, UploadFile, Depends)
from src.backend.app.services.resume_text_extractor import (extract_resume_text,)
from src.backend.app.schemas.recommendation import (RecommendationRequest,RecommendationResponse)
from sqlalchemy.orm import Session
from src.backend.app.database.session import (get_db)
from src.backend.app.services.resume_persistence_service import (save_resume_analysis)
from src.backend.app.services.recommendation_service import (analyze_career_text, analyze_personalized_career_text)
router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)
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
):
    if top_k < 1 or top_k > 5:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 5.",
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
            user_id=user_id,
            filename=file.filename or "",
            extracted_text=text,
            extracted_skills=result[
                "extracted_skills"
            ],
            recommendations=result[
                "recommendations"
            ],
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