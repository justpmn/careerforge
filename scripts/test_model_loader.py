from src.recommendation.model_loader import (
    load_metadata,
    load_model,
    validate_model_resources,
)

def main():
    print("=" * 40)
    print("CareerForge Model Loader Test")
    print("=" * 40)
    print("\nLoading model...")
    model = load_model()
    print("Loading metadata...")
    metadata = load_metadata()
    print("Validating model resources...")
    validate_model_resources(
        model,
        metadata,
    )
    print("\nModel loaded successfully.")
    print("Model type:",type(model).__name__,)
    print("Features:",model.n_features_in_,)
    print("Career classes:",len(model.classes_),)
    print("Model version:",metadata["version"],)
    print("\nValidation successful.")
if __name__ == "__main__":
    main()