from src.preprocessing.skill_extractor import (
    extract_skills,
)

from src.preprocessing.spacy_skill_extractor import (
    extract_spacy_skills,
)


SAMPLE_RESUME = """
P E T E R N Y A M U

Undergraduate Computer Science student with
skills in backend web development, MySQL,
and IT troubleshooting.

Technical Skills:
JavaScript, Node.js, Express.js, React,
REST APIs, HTML/CSS, Python, Git/GitHub.

Built and maintained backend applications
using Node.js and Express.js.

Responsible for database design and
management using MySQL.
"""


def main():
    regex_skills = set(
        extract_skills(
            SAMPLE_RESUME
        )
    )

    spacy_skills = set(
        extract_spacy_skills(
            SAMPLE_RESUME
        )
    )

    common = (
        regex_skills
        & spacy_skills
    )

    regex_only = (
        regex_skills
        - spacy_skills
    )

    spacy_only = (
        spacy_skills
        - regex_skills
    )

    print("=" * 50)
    print("CareerForge Skill Extractor Comparison")
    print("=" * 50)

    print("\nCurrent extractor:")
    for skill in sorted(regex_skills):
        print("-", skill)

    print("\nspaCy extractor:")
    for skill in sorted(spacy_skills):
        print("-", skill)

    print("\nFound by both:")
    for skill in sorted(common):
        print("-", skill)

    print("\nCurrent extractor only:")
    for skill in sorted(regex_only):
        print("-", skill)

    print("\nspaCy only:")
    for skill in sorted(spacy_only):
        print("-", skill)


if __name__ == "__main__":
    main()