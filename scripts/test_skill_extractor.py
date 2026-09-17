from src.preprocessing.skill_extractor import (extract_skill_matches, extract_skills)

SAMPLE_RESUME = """
Backend Software Engineer

Experienced backend developer with strong Python
and FastAPI development skills.

Built REST APIs backed by PostgreSQL and Redis.
Containerized applications using Docker and
deployed services to AWS.

Worked with Git, Linux, JavaScript and TypeScript.
Experience developing microservices and cloud
applications.

Programming languages and technologies:
Python, SQL, Go, JavaScript, TypeScript.
"""

def main():
    print("Resume Skill extractor: Test")
    print("_________________________________________________")
    
    matches = extract_skill_matches(SAMPLE_RESUME)
    skills = extract_skills(SAMPLE_RESUME)
    
    print("\n Matches:")
    print("-------------------------------")
    if matches.empty:
        print("No skills detected")
    else:
        print(matches.to_string(index=False))
        
        print("\n Canonical skills:")
        print("-------------------------------")
        for  skill in skills:
            print(f" - {skill}")
            
        print("\n_________________________________________________")
        print("Test completed")

if __name__ == "__main__":
    main()
