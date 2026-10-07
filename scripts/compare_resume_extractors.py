import sys
from pathlib import Path

from src.backend.app.services.resume_text_extractor import (
    extract_resume_text,
)
from src.preprocessing.skill_extractor import (
    extract_skills,
)
from src.preprocessing.spacy_skill_extractor import (
    extract_spacy_skills,
)


def main():
    if len(sys.argv) < 2:
        raise ValueError(
            "Provide a resume path.\n"
            "Example: python -m scripts.compare_resume_extractors resume.pdf"
        )

    resume_path = Path(sys.argv[1])

    if not resume_path.exists():
        raise FileNotFoundError(
            f"Resume not found: {resume_path}"
        )

    file_bytes = resume_path.read_bytes()

    text = extract_resume_text(
        filename=resume_path.name,
        file_bytes=file_bytes,
    )

    current_skills = set(
        extract_skills(text)
    )

    spacy_skills = set(
        extract_spacy_skills(text)
    )

    common = current_skills & spacy_skills
    current_only = current_skills - spacy_skills
    spacy_only = spacy_skills - current_skills

    print("=" * 55)
    print("CareerForge Real Resume Extractor Comparison")
    print("=" * 55)

    print("\nResume:")
    print(resume_path.name)

    print("\nCurrent extractor:")
    for skill in sorted(current_skills):
        print("-", skill)

    print("\nspaCy extractor:")
    for skill in sorted(spacy_skills):
        print("-", skill)

    print("\nFound by both:")
    for skill in sorted(common):
        print("-", skill)

    print("\nCurrent extractor only:")
    for skill in sorted(current_only):
        print("-", skill)

    print("\nspaCy only:")
    for skill in sorted(spacy_only):
        print("-", skill)


if __name__ == "__main__":
    main()