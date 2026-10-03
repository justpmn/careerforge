from src.recommendation.feature_vector import (build_feature_vector)
from src.recommendation.model_loader import (load_metadata,load_model, validate_model_resources)

class CareerRecommender:
    def __init__(self):
        self.model = load_model()
        self.metadata = load_metadata()

        validate_model_resources(
            self.model,
            self.metadata,
        )

        self.feature_names = self.metadata[
            "feature_names"
        ]
    def predict(
        self,
        skills: list[str],
        top_k: int = 3,
    ) -> list[dict]:
        feature_vector = build_feature_vector(
            skills,
            self.feature_names,
        )

        active_features = int(
            feature_vector.sum(axis=1).iloc[0]
        )
        if active_features == 0:
            raise ValueError(
                "None of the supplied skills matched "
                "the Random Forest feature vocabulary."
            )

        probabilities = (
            self.model.predict_proba(
                feature_vector
            )[0]
        )
        ranked_indices = (
            probabilities.argsort()[::-1]
        )
        top_k = min(
            top_k,
            len(self.model.classes_),
        )
        recommendations = []

        for rank, index in enumerate(
            ranked_indices[:top_k],
            start=1,
        ):
            recommendations.append(
                {
                    "rank": rank,
                    "career_key": (
                        self.model.classes_[
                            index
                        ]
                    ),
                    "score": float(
                        probabilities[index]
                    ),
                }
            )
        return recommendations