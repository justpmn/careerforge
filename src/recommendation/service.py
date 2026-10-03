from src.preprocessing.skill_extractor import (
    extract_skills,
)

from src.recommendation.predictor import (
    CareerRecommender,
)


class CareerRecommendationService:
    def __init__(self):
        self.recommender = CareerRecommender()

        self.model_feature_lookup = {
            feature.casefold(): feature
            for feature
            in self.recommender.feature_names
        }

    def recommend_from_text(
        self,
        text: str,
        top_k: int = 3,
    ) -> dict:
        """
        Extract skills from raw text and generate
        ranked CareerForge career recommendations.
        """

        extracted_skills = extract_skills(
            text
        )

        model_skills = []

        ignored_skills = []

        for skill in extracted_skills:
            if (
                skill.casefold()
                in self.model_feature_lookup
            ):
                model_skills.append(skill)
            else:
                ignored_skills.append(skill)

        if not model_skills:
            raise ValueError(
                "Skills were extracted, but none matched "
                "the Random Forest feature vocabulary."
            )

        recommendations = (
            self.recommender.predict(
                model_skills,
                top_k=top_k,
            )
        )

        return {
            "extracted_skills":
                extracted_skills,

            "model_skills":
                model_skills,

            "ignored_skills":
                ignored_skills,

            "recommendations":
                recommendations,
        }