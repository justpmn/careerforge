from scripts.build_vocabulary import main as build_vocabulary
from scripts.build_career_skills import main as build_career_skills
from scripts.audit_skill_graph import main as audit_skill_graph

def main():
    print("\nStarting preprocessing pipeline...")
    print("\n____________________________________________________")
    print("\n[1/3] Building skill vocabulary...")
    build_vocabulary()
    print("\n[2/3] Building career skills...")
    build_career_skills()
    print("\n[3/3] Auditing skill graph...")
    audit_skill_graph()
    print("\nPreprocessing pipeline complete.")
if __name__ == "__main__":
    main()