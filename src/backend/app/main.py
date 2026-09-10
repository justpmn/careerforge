from fastapi import FastAPI

app = FastAPI(
    title="CareerForge API",
    description="Backend API for the AI Career Mentorship System",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "CareerForge API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }