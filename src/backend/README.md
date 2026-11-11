
# CareerForge Backend

The CareerForge backend is a Python-based REST API built with FastAPI. It provides authentication, career recommendations, competency assessments, personalized learning roadmaps, AI-powered mentorship, and administrative functionality.

The backend integrates a Random Forest career recommendation model, PostgreSQL for persistent storage, and configurable language model providers for conversational career guidance.

**Production API:** https://api.careerforgeapp.me
**API Documentation (local):** http://127.0.0.1:8000/docs
**Main Project:** [CareerForge](../../README.md)

## 1. Technology Stack

| Category | Technology |
|---|---|
| Language | Python |
| Web Framework | FastAPI |
| Data Validation | Pydantic |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Migrations | Alembic |
| Machine Learning | Scikit-learn |
| Data Processing | Pandas, NumPy |
| Model Serialization | Joblib |
| HTTP Client | HTTPX |
| Authentication | JWT, OAuth 2.0 |
| Password Hashing | Argon2 |
| Cloud LLM | Cloudflare Workers AI |
| Local LLM | Ollama |
| Testing | Pytest, unittest |
| Deployment | Microsoft Azure, systemd |

## 2. Backend Architecture

The backend separates request handling, application logic, database operations, and machine learning inference.

```mermaid
flowchart TD
    A[React Frontend] --> B[FastAPI Router]
    B --> C[Authentication and Authorization]
    B --> D[Application Services]

    D --> E[Career Recommendation]
    D --> F[Competency Assessment]
    D --> G[Learning Roadmaps]
    D --> H[AI Mentor]

    E --> I[Random Forest Model]
    F --> J[(PostgreSQL)]
    G --> J
    H --> J

    H --> K{LLM Provider}
    K --> L[Cloudflare Workers AI]
    K --> M[Local Ollama]
```

The API routes validate incoming requests and delegate application operations to service modules. SQLAlchemy handles relational persistence, while the recommendation and AI Mentor services handle model inference.

## 3. Directory Structure

The primary backend application is located in `src/backend/app/`.

```text
src/backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   ├── auth.py
│   │   ├── admin_auth.py
│   │   └── router.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── tokens.py
│   │   └── admin_logging.py
│   │
│   ├── database/
│   │   ├── models/
│   │   ├── base.py
│   │   └── session.py
│   │
│   ├── schemas/
│   ├── services/
│   ├── resource_catalog/
│   └── main.py
│
└── README.md
```

Other backend-related files are located at the repository root:

| Path | Purpose |
|---|---|
| `requirements.txt` | Python dependencies |
| `migrations/` | Alembic database migrations |
| `alembic.ini` | Migration configuration |
| `scripts/` | Data preparation, seeding, and development utilities |
| `src/preprocessing/` | Skill extraction and preprocessing |
| `src/recommendation/` | Model loading, feature generation, and inference |
| `models/` | Random Forest metadata and expected model artifacts |
| `tests/` | Backend tests |
| `docker-compose.yml` | Local PostgreSQL service |

### Main Application Components

**API Routes:** Define HTTP endpoints, request validation, authentication requirements, and response handling.

**Services:** Contain application logic for recommendations, assessments, career preferences, learning resources, AI mentorship, and administration.

**Database:** Contains SQLAlchemy models, session management, and database integration.

**Core:** Contains application configuration, security utilities, token management, and operational logging.

**Schemas:** Define data structures used in request and response validation.

## 4. Local Installation

All commands in this section should be executed from the repository root unless otherwise specified.

### Prerequisites

- Python with pip and virtual environment support
- PostgreSQL 17 or a compatible PostgreSQL installation
- Git
- Docker and Docker Compose (optional)
- Ollama (optional for local AI inference)

### Clone the Repository

```bash
git clone https://github.com/justpmn/careerforge.git
cd careerforge
```

### Create a Virtual Environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The dependency file is maintained at the repository root, not inside `src/backend`.

## 5. Environment Configuration

CareerForge uses Pydantic Settings to read its configuration from environment variables and the root `.env` file.

Create the environment file:

Windows:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Review the generated `.env` and provide the required credentials.

### Main Environment Variables

| Variable | Description |
|---|---|
| `APP_NAME` | API application name |
| `APP_VERSION` | Application version |
| `DEBUG` | Debug configuration |
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Secret used to sign access tokens |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration period |
| `OAUTH_STATE_SECRET_KEY` | Secret used for OAuth session state |
| `COOKIE_SECURE` | Enables secure cookies |
| `FRONTEND_PUBLIC_ORIGIN` | Public frontend origin |
| `OAUTH_REDIRECT_ORIGIN` | OAuth callback redirect origin |
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth secret |
| `GITHUB_OAUTH_CLIENT_ID` | GitHub OAuth client ID |
| `GITHUB_OAUTH_CLIENT_SECRET` | GitHub OAuth secret |
| `EMAIL_DELIVERY_MODE` | Email delivery configuration |
| `EMAIL_SENDER_ADDRESS` | Email sender address |
| `BREVO_API_KEY` | Brevo email service API key |
| `MFA_ENCRYPTION_KEY` | Administrative MFA encryption key |
| `MFA_ISSUER` | Authenticator issuer name |
| `LLM_PROVIDER` | Selected language model provider |

The backend requires `OAUTH_STATE_SECRET_KEY` to contain at least 32 UTF-8 bytes before startup.

For local development, configure:

```dotenv
DEBUG=true
COOKIE_SECURE=false
FRONTEND_PUBLIC_ORIGIN=http://localhost:5173
OAUTH_REDIRECT_ORIGIN=http://localhost:5173
```

Use secure credentials for all secrets. Generate your own values rather than copying credentials from another environment.

**Never commit `.env`, access tokens, passwords, or API keys.**

## 6. Database Setup

CareerForge uses PostgreSQL with SQLAlchemy for persistence and Alembic for schema migrations.

### Option A: PostgreSQL with Docker

The repository includes a Docker Compose configuration for PostgreSQL.

Ensure `.env` contains matching values:

```dotenv
POSTGRES_DB=careerforge
POSTGRES_USER=careerforge
POSTGRES_PASSWORD=YOUR_LOCAL_PASSWORD
DATABASE_URL=postgresql+psycopg://careerforge:YOUR_LOCAL_PASSWORD@localhost:5432/careerforge
```

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Check the container:

```bash
docker compose ps
```

### Option B: Existing PostgreSQL Installation

Create a local database and configure `DATABASE_URL` to reference it.

The expected SQLAlchemy connection format is:

```text
postgresql+psycopg://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

### Apply Database Migrations

```bash
python -m alembic upgrade head
```

Check the current migration revision:

```bash
python -m alembic current
```

Migration files are stored in `migrations/versions/`.

Do not run development migrations against a production database without reviewing the changes and taking appropriate backups.

### Reference Data

Database migrations create the schema but do not necessarily populate all career, skill, competency, and learning-resource records.

CareerForge includes scripts for preparing and importing reference data. For example:

```bash
python -m scripts.seed_learning_resources
```

This resource seed requires the corresponding canonical skills to exist in the database first.

Before running any seed script, inspect its prerequisites and target database. Use only the scripts appropriate for the intended development environment.

## 7. Running the API

From the repository root:

```bash
python -m uvicorn src.backend.app.main:app --reload --port 8000
```

The API will be available at:

- Root: http://127.0.0.1:8000/
- Health: http://127.0.0.1:8000/api/health
- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI specification: http://127.0.0.1:8000/openapi.json

The `--reload` flag is intended for local development.

A simple connectivity check:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{"status":"healthy"}
```

This basic health endpoint confirms that the API is responding. It does not independently verify database connectivity, machine learning inference, or third-party AI availability.

## 8. API Modules

Routes are registered through:

`src/backend/app/api/router.py`

All application API routes use the `/api` prefix.

| Route Group | Responsibility |
|---|---|
| `/api/auth` | Registration, login, logout, sessions |
| `/api/auth/oauth` | Google and GitHub authentication |
| `/api/recommendations` | Career recommendation and CV analysis |
| `/api/preferences` | Career preferences |
| `/api/ai-mentor` | AI conversations, history, and background jobs |
| `/api/admin` | Administrative monitoring and operations |
| `/api/health` | Basic API health check |

Additional route modules handle competency evidence, learning roadmaps, skill assessments, learning progress, account settings, resource administration, MFA, and account recovery.

Consult `/docs` for the full endpoint list and current request schemas.

### AI Mentor Endpoints

The following endpoints support persistent mentorship:

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/ai-mentor/jobs` | Queue a mentor response |
| GET | `/api/ai-mentor/jobs` | List recent generation jobs |
| GET | `/api/ai-mentor/jobs/{job_id}` | Check a job's status |
| GET | `/api/ai-mentor/conversations` | List conversations |
| GET | `/api/ai-mentor/conversations/{id}/messages` | Retrieve conversation history |
| PATCH | `/api/ai-mentor/conversations/{id}` | Rename a conversation |
| DELETE | `/api/ai-mentor/conversations/{id}` | Delete a conversation |

These endpoints require authentication.

## 9. Authentication and Authorization

CareerForge supports:

- Email and password registration
- Password hashing with Argon2
- JWT-based authentication
- HTTP-only authentication cookies
- CSRF protection
- Google and GitHub OAuth
- Email verification and password recovery
- Administrative authorization
- Time-based one-time password MFA for administrator accounts

The implementation is distributed across the authentication routes, API dependencies, and core security services.

Authentication and administrator authorization are enforced by the backend rather than relying solely on frontend route protection.

Production environments should use HTTPS, secure cookies, and properly configured OAuth callback URLs.

## 10. Career Recommendation System

The career recommendation pipeline is implemented primarily within:

```text
src/
├── preprocessing/
└── recommendation/
```

The application uses a Random Forest classifier to generate ranked technology career recommendations.

### Inference Workflow

```text
Uploaded CV
    |
    v
Text Extraction
    |
    v
Technical Skill Extraction
    |
    v
Feature Vocabulary Matching
    |
    v
Random Forest Classifier
    |
    v
Ranked Career Predictions
    |
    v
Preference-Aware Recommendations
```

Extracted skills are matched against the model's feature vocabulary and converted into the expected feature vector.

The classifier returns probability-based ranking scores for supported career categories.

These scores represent model outputs, not verified career readiness.

### Model Artifacts

The model loader expects:

```text
models/
├── careerforge_rf_v1.joblib
└── careerforge_rf_v1_metadata.json
```

The metadata contains the feature vocabulary, expected feature count, and career class information.

The loader validates that the model and metadata have compatible feature counts and career classes.

**Important:** Ensure the trained `.joblib` artifact is available in the expected location before using recommendation functionality. It may need to be obtained separately from the source repository.

The application does not automatically train a new Random Forest model on startup.

### Recommendation Services

Relevant modules include:

- `src/recommendation/model_loader.py`
- `src/recommendation/predictor.py`
- `src/recommendation/feature_vector.py`
- `src/recommendation/service.py`
- `src/backend/app/services/recommendation_service.py`

The backend also supports saved CV analysis, career preferences, skill coverage, and competency-based guidance.

## 11. Competency Assessment and Learning Roadmaps

CareerForge compares a user's recorded skills and submitted evidence with structured career competency profiles.

Relevant services include:

- `competency_gap_service.py`
- `ai_mentor_context_service.py`
- `careerforge_account_context_service.py`
- `learning_roadmap_service.py`
- `learning_resource_service.py`

Competency statuses distinguish different forms of skill evidence and assessment availability.

For example:

- `evidenced`: Matching skills were identified through recorded, non-manual skill sources.
- `evidence_found`: Relevant CV evidence exists for a competency requiring manual review.
- `self_reported`: A relevant skill was manually declared by the user.
- `not_assessed`: A competency has not yet been assessed through the relevant process.
- `not_evidenced`: Available recorded skills did not establish a match for the competency.

These statuses should not be interpreted as independent certification of professional proficiency.

Learning resources are associated with relevant skills and competencies, and the roadmap records user-reported progress separately from assessment evidence.

## 12. AI Career Mentor

CareerForge supports conversational career guidance using a configurable large language model provider.

The AI Mentor can receive structured context containing:

- The user's selected target career
- Recorded and self-reported skills
- Competency assessment results
- Saved career recommendations
- Learning roadmap information
- Available learning resources
- Recent conversation history

The backend constructs this context before submitting a request to the selected model.

### Provider Selection

**Local inference using Ollama:**

```dotenv
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3.5:4b
```

Install Ollama separately and ensure the configured model is present.

For example:

```bash
ollama pull qwen3.5:4b
```

**Cloud inference using Cloudflare Workers AI:**

```dotenv
LLM_PROVIDER=cloudflare
CLOUDFLARE_ACCOUNT_ID=YOUR_ACCOUNT_ID
CLOUDFLARE_AI_API_TOKEN=YOUR_PRIVATE_TOKEN
CLOUDFLARE_MODEL=@cf/google/gemma-4-26b-a4b-it
```

Cloudflare requires a valid account and a Workers AI API token with the appropriate permissions.

The backend sends the HTTP request to Cloudflare. API credentials must never be exposed in the React frontend.

### Relevant Modules

| Module | Purpose |
|---|---|
| `llm_service.py` | Message construction and inference provider selection |
| `assessment_mentor_service.py` | Competency-aware AI guidance |
| `ai_mentor_context_service.py` | Assessment context preparation |
| `careerforge_account_context_service.py` | Authenticated account context |
| `mentor_conversation_service.py` | Persistent conversations and messages |
| `mentor_job_service.py` | Background generation jobs |
| `llm_monitoring.py` | Inference duration and failure monitoring |
| `llm_health_service.py` | Provider health checks |

### Background Job Processing

The frontend can submit a mentor request without waiting for inference to finish in the initial HTTP request.

```mermaid
sequenceDiagram
    participant UI as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Worker as Mentor Worker
    participant LLM as LLM Provider

    UI->>API: POST /api/ai-mentor/jobs
    API->>DB: Save message and queued job
    API-->>UI: 202 Accepted
    Worker->>DB: Claim queued job
    Worker->>LLM: Generate response
    LLM-->>Worker: Generated answer
    Worker->>DB: Save response and job status
    UI->>API: Check job status
    API-->>UI: Completed
    UI->>API: Retrieve conversation messages
```

The worker is started during FastAPI's application lifespan.

Jobs transition through these statuses:

```text
queued -> running -> completed
                  -> failed
```

The worker also attempts to recover interrupted running jobs during application startup.

Job durations are recorded in seconds for monitoring and evaluation.

### Model Limitations

LLM-generated advice can contain inaccuracies. CareerForge instructs the model to ground advice in supplied application records, but generated claims should still be treated as advisory.

Resource recommendations should reference actual stored learning resources rather than invented links.

## 13. Logging and Monitoring

CareerForge records operational events to support debugging, evaluation, and administration.

The logging service is located at:

`src/backend/app/core/admin_logging.py`

Structured logs are stored under:

```text
logs/careerforge-system.jsonl
```

The logger supports rotation and records metadata such as:

- Event category and action
- Timestamp and severity
- HTTP status codes
- Error types
- Processing duration

Sensitive request content, CV text, account credentials, and AI conversations should not be included in operational telemetry.

The administrator health endpoint checks multiple backend components, including the database, recommendation model, and configured AI provider.

### AI Mentor Performance

The backend logs assessment preparation, context preparation, and inference timings separately.

This helps distinguish time spent generating a model response from time spent preparing account and competency data.

## 14. Testing

Backend tests are located primarily in `tests/` and `scripts/`.

Run the relevant non-destructive tests from the repository root:

```bash
python -m pytest tests
```

Some tests require additional environment configuration or a dedicated test database. Review the relevant test requirements before running the full suite.

### PostgreSQL Integration Tests

CareerForge includes an isolated local integration database named:

```text
careerforge_test
```

The preparation script validates that the target is local PostgreSQL before creating and migrating the test database.

```bash
python -m scripts.prepare_integration_database
```

Integration tests can then be run using:

```bash
python -m scripts.run_postgres_integration
```

These scripts are designed to avoid using the development or production database for destructive test operations.

Never set a test database URL to a production database or bypass the safety checks.

### Frontend End-to-End Tests

Browser-based integration tests use Playwright and are documented in the [Frontend README](../frontend/README.md).

## 15. Deployment

The production backend runs on an Azure-hosted Linux virtual machine.

The current deployment uses:

- Microsoft Azure for backend hosting
- systemd for service management
- Neon PostgreSQL for persistent data
- Cloudflare Workers AI for Gemma inference
- HTTPS through the configured API domain

### Production Considerations

Before deploying:

1. Verify application configuration and required secrets.
2. Ensure the database is available and migrations are current.
3. Confirm the expected Random Forest artifacts are installed.
4. Verify the configured AI inference provider.
5. Install the required Python dependencies.
6. Restart the backend service.
7. Check service logs and health endpoints.
8. Test authenticated application functionality.

On the configured production server, the service can be inspected with:

```bash
sudo systemctl status careerforge-api
```

Restart it with:

```bash
sudo systemctl restart careerforge-api
```

View recent logs:

```bash
sudo journalctl -u careerforge-api -n 50 --no-pager
```

The exact service configuration, environment paths, and deployment permissions depend on the server setup.

Do not commit production environment files or infrastructure credentials to the repository.

## 16. Troubleshooting

### Backend Fails During Startup

Verify that the root `.env` file exists and that `OAUTH_STATE_SECRET_KEY` is configured correctly.

### PostgreSQL Connection Failure

Check `DATABASE_URL`, database availability, credentials, and network accessibility.

### Recommendation Model Not Found

Confirm the existence of:

```text
models/careerforge_rf_v1.joblib
models/careerforge_rf_v1_metadata.json
```

The model and metadata must be compatible.

### Ollama Is Unavailable

Confirm that Ollama is running and the configured model is installed:

```bash
ollama list
```

### Cloudflare AI Requests Fail

Verify the Cloudflare Account ID, API token, model identifier, network connectivity, and provider usage limits.

### AI Mentor Responses Remain Queued

Check the mentor worker, database connectivity, backend process health, and job-related application logs.

### Frontend Cannot Reach the API

Verify that FastAPI is running on the expected port and that the frontend Vite proxy configuration points to the correct backend.

## 17. Development Guidelines

- Use service modules for application logic.
- Keep API routes focused on request validation and orchestration.
- Use Alembic for database schema changes.
- Do not commit secrets or sensitive user data.
- Add automated tests for new functionality.
- Preserve existing authentication and authorization checks.
- Keep AI inference provider configuration separate from frontend code.
- Use feature branches and meaningful Git commits.

## Related Documentation

- [Main Project README](../../README.md)
- [Frontend README](../frontend/README.md)

## Disclaimer

CareerForge provides AI-assisted career guidance and competency assessments for informational and educational purposes.

Recommendations, model scores, and AI-generated responses should not be treated as guarantees of employment or independently verified professional competence.
