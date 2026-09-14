import pandas as pd
from src.preprocessing.paths import PROCESSED_DATA_DIR

def main():
    career_skills_path = (PROCESSED_DATA_DIR / "career_skills.csv")
    aliases_path = (PROCESSED_DATA_DIR / "skill_aliases.csv")
    career_skills = pd.read_csv(career_skills_path)
    aliases = pd.read_csv(aliases_path)
    both_sources = ((career_skills["source_onet"] == 1) & (career_skills["source_stackoverflow"] == 0)).sum()
    
    onet_only = ((career_skills["source_onet"] == 1) & career_skills["source_stackoverflow"] == 0).sum()
    stackoverflow_only = ((career_skills["source_onet"] == 0) & (career_skills["source_stackoverflow"] == 1)).sum()
    
    print("\n Skill Graph audit ")
    print(f"Both sources: {both_sources}")
    print(f"stack Overflow only: {stackoverflow_only}")
    print(f"O*NET only: {onet_only}")
    print(f"\nTotal graph edges: {len(career_skills)}")
    print(f"Unique Careers: {career_skills['career_key'].nunique}")
    print(f"Unique skills:  {career_skills['canonical_skill'].nunique()}" )
    print(f"Skill aliases: {len(aliases)}")
    
if __name__ == "__main__":
    main()