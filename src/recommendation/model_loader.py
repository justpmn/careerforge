import json
from pathlib import Path
import joblib
from src.preprocessing.paths import PROJECT_ROOT


MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "careerforge_rf_v1.joblib"
)

METADATA_PATH = (
    PROJECT_ROOT
    / "models"
    / "careerforge_rf_v1_metadata.json"
)


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Random Forest model not found: {MODEL_PATH}"
        )

    model = joblib.load(MODEL_PATH)

    return model

def load_metadata() -> dict:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Model metadata not found: {METADATA_PATH}"
        )

    with open(
        METADATA_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        metadata = json.load(file)

    return metadata

def validate_model_resources(
    model,
    metadata: dict,
) -> None:
    expected_feature_count = metadata["feature_count"]
    model_feature_count = model.n_features_in_
    if model_feature_count != expected_feature_count:
        raise ValueError(
            "Model feature count does not match metadata. "
            f"Model expects {model_feature_count}, "
            f"metadata contains {expected_feature_count}."
        )
    metadata_classes = metadata["career_classes"]
    model_classes = model.classes_.tolist()
    if model_classes != metadata_classes:
        raise ValueError("Model career classes do not match metadata.")