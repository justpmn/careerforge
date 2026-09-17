import pandas as pd
from src.preprocessing.training_data import (STACKOVERFLOW_PATH)

KEYWORDS = [
    "AI",
    "machine",
    "data",
    "UX",
    "UI",
    "design",
]

def main():
    data = pd.read_csv(
        STACKOVERFLOW_PATH,
        usecols=["DevType"],
        low_memory=False,
    )

    devtypes = (
        data["DevType"]
        .dropna()
        .astype(str)
        .value_counts()
    )

    print("\nRelevant Stack Overflow DevType values")
    print("=" * 55)

    for devtype, count in devtypes.items():

        if any(
            keyword.casefold()
            in devtype.casefold()
            for keyword in KEYWORDS
        ):
            print(
                f"{count:>6}  {devtype}"
            )

if __name__ == "__main__":
    main()