import pandas as pd

def build_feature_vector(
    skills: list[str],
    feature_names: list[str],
) -> pd.DataFrame:
    feature_lookup = {
        feature.casefold(): feature
        for feature in feature_names
    }

    matched_features = set()

    for skill in skills:
        normalized_skill = skill.strip().casefold()

        matched_feature = feature_lookup.get(
            normalized_skill
        )

        if matched_feature:
            matched_features.add(
                matched_feature
            )

    vector = {
        feature: int(
            feature in matched_features
        )
        for feature in feature_names
    }

    return pd.DataFrame(
        [vector],
        columns=feature_names,
    )