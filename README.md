# CareerForge

CareerForge is an AI-powered career mentorship and recommendation system designed to help users identify suitable career paths based on their skills, experience, and resume information.

The system uses resume analysis, career and skill data, machine learning, and a structured backend to generate personalized career recommendations and identify skill gaps between a user's current profile and potential career paths.

## Project Overview

Choosing a suitable career path can be difficult, especially when users are unsure how their existing skills and experience relate to different professions.

CareerForge aims to address this problem by providing a centralized platform that can:

- Analyze user resumes.
- Identify relevant skills.
- Recommend suitable career paths.
- Identify skill gaps.
- Provide learning resources for missing skills.
- Support career guidance through an AI mentorship component.
- Store recommendation and mentorship history for future reference.

## System Architecture

CareerForge follows a modular architecture consisting of several major components:

1. **Frontend**  
   Provides the user interface through which users interact with the system.

2. **Backend API**  
   Handles application logic, user requests, database communication, resume processing, and recommendation services.

3. **Database**  
   Stores users, careers, skills, resumes, recommendations, skill gaps, learning resources, and mentorship information.

4. **Resume Processing**  
   Extracts and processes information from uploaded resumes for use in career analysis.

5. **Career Recommendation Model**  
   Uses machine learning to estimate suitable career categories based on processed resume information.

6. **AI Mentor**  
   Provides conversational career guidance and allows users to ask follow-up questions about their career recommendations.

## Technology Stack

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

### Database

- PostgreSQL

### Machine Learning and Data Processing

- Scikit-learn
- Pandas
- NumPy
- Joblib

### Development Tools

- Git
- GitHub
- Visual Studio Code
- Jupyter Notebook

## Project Structure

```text
careerforge/
│
├── app/
│   ├── main.py
│   ├── models/
│   ├── schemas/
│   ├── routes/
│   ├── services/
│   └── database/
│
├── src/
│   ├── preprocessing/
│   └── recommendation/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── alembic/
│
├── tests/
│
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

The exact structure may change as development continues.

## Database Design

The PostgreSQL database contains the main entities required by the CareerForge system.

Current database tables include:

- `users`
- `resumes`
- `careers`
- `skills`
- `career_skills`
- `user_skills`
- `recommendations`
- `skill_gaps`
- `learning_resources`
- `learning_resource_skills`
- `mentor_conversations`
- `mentor_messages`
- `alembic_version`

SQLAlchemy is used as the Object Relational Mapper (ORM), while Alembic manages database schema migrations.

## Career Recommendation Model

CareerForge uses a machine learning classifier to predict career categories from processed resume information.

The current recommendation pipeline uses a **Random Forest classifier** as the primary model.

Resume text is transformed into numerical features before being passed to the classifier. The model produces probabilities for possible career categories, allowing the system to return multiple career recommendations rather than only a single prediction.

The model is evaluated using metrics including:

- Accuracy
- Balanced Accuracy
- Macro F1 Score
- Weighted F1 Score
- Top-3 Accuracy
- Log Loss

Several Random Forest configurations have been tested to compare generalization performance and reduce overfitting.

## Data Sources

CareerForge uses multiple datasets to support career recommendation, skill mapping, and career information.

### Resume Dataset

A resume dataset containing approximately 22,000 samples is used for developing the career recommendation model.

The dataset contains resume-related text and associated career information that can be transformed into training data for the recommendation system.

### O*NET

O*NET data is used as a source of structured occupational information, including:

- Occupations
- Skills
- Knowledge areas
- Abilities
- Career requirements

This information supports career-to-skill mapping and skill-gap analysis.

### Stack Overflow Developer Data

Stack Overflow developer data can be used to supplement technical career and skill information, particularly for computing and software-related career paths.

## Resume Processing

The resume processing pipeline is responsible for preparing resume information for analysis.

The general workflow is:

```text
Resume Upload
      |
      v
Text Extraction
      |
      v
Text Cleaning and Preprocessing
      |
      v
Feature Extraction
      |
      v
Career Recommendation Model
      |
      v
Top Career Recommendations
```

The extracted information can also be used to identify user skills and compare them against the requirements of recommended careers.

## Skill Gap Analysis

CareerForge compares the skills identified from a user's profile with the skills associated with a recommended career.

Conceptually:

```text
Required Career Skills
          -
Current User Skills
          =
Missing Skills
```

The resulting missing skills form the user's skill gap.

CareerForge can then associate these gaps with relevant learning resources to help users understand what they need to learn to move toward a particular career.

## Recommendation Workflow

The intended recommendation process is:

```text
User
  |
  v
Upload Resume
  |
  v
Resume Text Extraction
  |
  v
Resume Preprocessing
  |
  v
Career Recommendation Model
  |
  v
Top Career Predictions
  |
  v
Career and Skill Mapping
  |
  v
Skill Gap Analysis
  |
  v
Learning Resources
  |
  v
AI Career Mentor
```

## Current Development Status

CareerForge is currently under active development.

Implemented or actively developed components include:

- Backend project structure
- PostgreSQL database
- SQLAlchemy database models
- Alembic migrations
- Career and skill database entities
- Dataset loading and preprocessing
- Resume dataset exploration
- Career recommendation model experimentation
- Random Forest model training and evaluation
- Resume text extraction pipeline

Additional components will be integrated as development progresses.

## Planned Features

Future development includes:

- Complete frontend integration
- User authentication and profile management
- Resume upload interface
- Automated skill extraction
- Top career recommendation display
- Career confidence scores
- Skill-gap visualization
- Learning resource recommendations
- AI career mentor integration
- Recommendation history
- Administrative dashboard
- End-to-end system integration and testing

## Installation

Clone the repository:

```bash
git clone https://github.com/justpmn/careerforge.git
cd careerforge
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment on Windows:

```bash
.venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Database Setup

CareerForge uses PostgreSQL.

Create a PostgreSQL database for the project and configure the required database credentials using the project's environment configuration.

Run the Alembic migrations:

```bash
alembic upgrade head
```

This creates or updates the database schema to the latest version.

## Running the Backend

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The backend will then be available locally through the configured FastAPI development server.

FastAPI's interactive API documentation can be used during development to inspect and test available endpoints.

## Development Workflow

Development is organized using feature branches for the major components of the system.

Examples include:

```text
feat/backend
feat/database
feat/dataset-preprocessing
feat/recommendation-model
feat/resume-text-extraction
feat/frontend
feat/integration
docs/README
```

Changes are developed and tested within their respective branches before being integrated into the main branch.

## Project Objectives

The main objectives of CareerForge are to:

1. Develop a system capable of analyzing resume information.
2. Build a machine learning model for career recommendation.
3. Identify skill gaps between users and recommended careers.
4. Recommend relevant learning resources.
5. Provide AI-assisted career mentorship.
6. Maintain user recommendation and mentorship history.
7. Provide an accessible interface for career exploration and guidance.

## Disclaimer

CareerForge is an academic project and is currently under development. Career recommendations generated by the system are intended to provide guidance and should not be treated as definitive career decisions.

## License

This project is currently developed for academic purposes.