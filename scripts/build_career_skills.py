from src.preprocessing.career_skills import save_career_skill_datasets

def main():
    onet_path, stackoverflow_path, combined_path, = save_career_skill_datasets()
    print("\n Career skill build completed. ")
    print(f"O*NET edges:{onet_path}")
    print(f"Stack overflow edges: {stackoverflow_path}")
    print(f"Combined graph edges: {combined_path}")
    
if __name__ == "__main__":
    main()