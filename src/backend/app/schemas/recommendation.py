from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=5,
    )


class CareerRecommendation(BaseModel):
    rank: int
    career_key: str
    score: float


class RecommendationResponse(BaseModel):
    extracted_skills: list[str]
    model_skills: list[str]
    ignored_skills: list[str]
    recommendations: list[CareerRecommendation]