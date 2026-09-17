from src.preprocessing.vocabulary import save_skill_datasets

def main():
    catalog_path, vocabulary_path, aliases_path = save_skill_datasets()
    print("\nSkill vocabulary build complete.")
    print(f"Skill catalog: {catalog_path}")
    print(f"Skill vocabulary {vocabulary_path}")
    print(f"Skill aliases{aliases_path}")
    
if __name__ == "__main__":
    main()