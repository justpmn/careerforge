from src.recommendation.feature_vector import (build_feature_vector)
from src.recommendation.model_loader import (load_metadata)
def main():
    metadata = load_metadata()
    feature_names = metadata["feature_names"]
    test_skills = [
        "Python",
        "PostgreSQL",
        "Docker",
        "SQL",
    ]
    vector = build_feature_vector(
        test_skills,
        feature_names,
    )
    print("=" * 40)
    print("CareerForge Feature Vector Test")
    print("=" * 40)
    print("\nVector shape:", vector.shape)
    print("Active features:",int(vector.sum(axis=1).iloc[0]))
    active_skills = (
        vector.columns[
            vector.iloc[0] == 1
        ].tolist()
    )

    print("Matched skills:",active_skills)
if __name__ == "__main__":
    main()