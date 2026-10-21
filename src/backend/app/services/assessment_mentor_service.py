
from sqlalchemy.orm import Session
from src.backend.app.services.competency_gap_service import (analyze_competency_gaps)
from src.backend.app.services.ai_mentor_context_service import (build_mentor_context)
from src.backend.app.services.llm_service import (generate_mentor_response)

async def generate_assessment_mentor_response(
    db: Session,
    user_id: int,
    career_key: str,
    message: str,
) -> str:

    assessment = analyze_competency_gaps(
        db=db,
        user_id=user_id,
        career_key=career_key,
    )

    context = build_mentor_context(assessment)

    response = await generate_mentor_response(
        message=message,
        context=context,
    )

    return response
