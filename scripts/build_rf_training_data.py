import pandas as pd
from src.preprocessing.paths import (PROCESSED_DATA_DIR)
from src.preprocessing.training_data import (EXPECTED_CAREERS,save_rf_training_dataset)

def main():
    print("\n========================================")
    print("Random Forest Train set Builder")
    print("========================================")

    (
        training_path,
        features_path,
        distribution_path,
    ) = save_rf_training_dataset()

    training = pd.read_parquet(training_path)
    distribution = pd.read_csv(distribution_path)
    feature_count = (len(training.columns) - 2)
    careers_found = set(distribution["career_key"])
    missing_careers = (EXPECTED_CAREERS - careers_found)
    print(f"\nTraining respondents: " f"{len(training):,}")
    print(f"RF skill features: " f"{feature_count:,}")
    print(f"Career classes: " f"{len(careers_found)}")
    print("\nClass distribution:")
    print(distribution.to_string(index=False))
    if missing_careers:
        print("\nWARNING: Missing CareerForge classes:")
        for career in sorted(missing_careers):
            print(f" - {career}")
    else:
        print("\nAll 22 CareerForge classes are present.")
    print("\nSaved:")
    print(training_path)
    print(features_path)
    print(distribution_path)

    print("\n========================================")
    print(" RF training dataset build complete")
    print("========================================")

if __name__ == "__main__":
    main()