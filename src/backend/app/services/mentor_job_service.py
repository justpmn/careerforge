
import asyncio
import logging

from time import perf_counter

from sqlalchemy import select, update

from src.backend.app.database.session import SessionLocal
from src.backend.app.database.models.mentor import MentorMessage
from src.backend.app.database.models.mentor_job import MentorGenerationJob
from src.backend.app.services.assessment_mentor_service import (
    generate_persistent_assessment_mentor_response,
)

logger = logging.getLogger("uvicorn.error")


def recover_interrupted_mentor_jobs() -> None:
    with SessionLocal() as db:
        db.execute(
            update(MentorGenerationJob)
            .where(MentorGenerationJob.status == "running")
            .values(status="queued")
        )
        db.commit()


def claim_next_mentor_job() -> int | None:
    with SessionLocal() as db:
        job = db.scalar(
            select(MentorGenerationJob)
            .where(MentorGenerationJob.status == "queued")
            .order_by(MentorGenerationJob.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )

        if job is None:
            return None

        job.status = "running"
        job_id = job.id
        db.commit()
        return job_id


async def process_mentor_job(job_id: int) -> None:
    started = perf_counter()

    try:
        with SessionLocal() as db:
            job = db.get(MentorGenerationJob, job_id)

            if job is None:
                return

            message = db.get(MentorMessage, job.user_message_id)

            if message is None or message.role != "user":
                raise ValueError("Queued user message was not found.")

            await generate_persistent_assessment_mentor_response(
                db=db,
                user_id=job.user_id,
                career_key=job.career_key,
                message=message.content,
                conversation_id=job.conversation_id,
                pre_saved_user_message_id=message.id,
            )

            job.status = "completed"
            job.response_seconds = perf_counter() - started
            job.error = None

            db.commit()

        logger.info(
            "CareerForge mentor job %s completed in %.2fs",
            job_id,
            perf_counter() - started,
        )

    except asyncio.CancelledError:
        raise

    except Exception:
        logger.exception("CareerForge mentor job %s failed", job_id)

        with SessionLocal() as db:
            job = db.get(MentorGenerationJob, job_id)

            if job is not None:
                job.status = "failed"
                job.error = (
                    "The AI Mentor could not respond. Please try again."
                )
                db.commit()


async def mentor_job_worker() -> None:
    while True:
        try:
            job_id = claim_next_mentor_job()

            if job_id is None:
                await asyncio.sleep(1.5)
                continue

            await process_mentor_job(job_id)

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception("CareerForge mentor worker error")
            await asyncio.sleep(3)
