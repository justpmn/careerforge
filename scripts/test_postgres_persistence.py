
"""
CareerForge PostgreSQL persistence integration tests.

Uses actual FastAPI routes and committed PostgreSQL writes.

Safety:
- Runs only against local careerforge_test.
- Creates uniquely named test users.
- Deletes only records belonging to those test users.
- Does not modify the development database.
"""

import unittest
import os
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, text
from sqlalchemy.engine import make_url
from src.backend.app.core.config import settings
from unittest.mock import AsyncMock, patch
from src.backend.app.database.models.mentor import (MentorConversation,  MentorMessage)
from scripts.test_resume_extraction import (create_test_docx, create_test_pdf)
from src.backend.app.database.models.resume import Resume
from src.backend.app.database.models.recommendation import Recommendation
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.user_skill import UserSkill


# Check the target BEFORE importing application/database modules.
url = make_url(settings.database_url)

if (
    url.drivername != "postgresql+psycopg"
    or url.database != "careerforge_test"
    or url.host not in {"localhost", "127.0.0.1", "::1"}
    or url.port not in {None, 5432}
):
    raise RuntimeError(
        "Persistence tests require local careerforge_test."
    )


from src.backend.app.main import app
from src.backend.app.database.session import (
    engine,
    SessionLocal,
)
from src.backend.app.database.models.user import User
from src.backend.app.database.models.career import Career
from src.backend.app.database.models.user_competency_assessment import (
    UserCompetencyAssessment,
)
from src.backend.app.database.models.user_learning_progress import (
    UserLearningProgress,
)
from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)


CAREER_KEY = "data_engineer"
PASSWORD = "CareerForge-Test-Password-2026!"
EMAIL_PREFIX = "cf-persistence-"


class TestPostgresPersistence(unittest.TestCase):

    def setUp(self):
        with engine.connect() as connection:
            database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        if database != "careerforge_test":
            raise RuntimeError(
                "Database safety check failed."
            )

        self.created_user_ids = []
        self.client = TestClient(app)

        self.addCleanup(self.cleanup_test_records)

        with SessionLocal() as db:
            career = db.scalar(
                select(Career).where(
                    Career.career_key == CAREER_KEY
                )
            )

            self.assertIsNotNone(
                career,
                "Seed Data Engineer before running these tests.",
            )

            self.career_id = career.id

        profile = CAREER_COMPETENCY_PROFILES[CAREER_KEY]

        self.assertTrue(profile)

        self.competency_key = profile[0]["key"]

        self.user_a = self.create_user("User A")
        self.user_b = self.create_user("User B")

    def cleanup_test_records(self):
        """
        Remove only accounts created by this test.
        """

        try:
            if not self.created_user_ids:
                return

            with SessionLocal() as db:
                for user_id in self.created_user_ids:
                    user = db.get(User, user_id)

                    if user is None:
                        continue

                    if not user.email.startswith(EMAIL_PREFIX):
                        raise RuntimeError(
                            "Refusing to delete a non-test account."
                        )

                    db.execute(
                        delete(UserCompetencyAssessment).where(
                            UserCompetencyAssessment.user_id
                            == user_id
                        )
                    )

                    db.execute(
                        delete(UserLearningProgress).where(
                            UserLearningProgress.user_id
                            == user_id
                        )
                    )
                    
                    # Remove only mentor records owned by
                    # the temporary integration-test user.
                    conversation_ids = db.scalars(
                        select(MentorConversation.id).where(
                            MentorConversation.user_id == user_id
                        )
                    ).all()

                    if conversation_ids:
                        db.execute(
                            delete(MentorMessage).where(
                                MentorMessage.conversation_id.in_(
                                    conversation_ids
                                )
                            )
                        )

                        db.execute(
                            delete(MentorConversation).where(
                                MentorConversation.user_id == user_id
                            )
                        )
                                            # Clean up CV integration records belonging
                    # exclusively to the temporary test user.
                    db.execute(
                        delete(Recommendation).where(
                            Recommendation.user_id == user_id
                        )
                    )

                    db.execute(
                        delete(UserSkill).where(
                            UserSkill.user_id == user_id
                        )
                    )

                    db.execute(
                        delete(Resume).where(
                            Resume.user_id == user_id
                        )
                    )


                    db.delete(user)

                db.commit()

        finally:
            self.client.close()

    def create_user(self, name):
        email = (
            f"{EMAIL_PREFIX}{uuid4().hex}@example.com"
        )

        registration = self.client.post(
            "/api/auth/register",
            json={
                "full_name": name,
                "email": email,
                "password": PASSWORD,
            },
        )

        if registration.status_code == 201:
            self.created_user_ids.append(
                registration.json()["id"]
            )

        self.assertEqual(
            registration.status_code,
            201,
            registration.text,
        )
        with SessionLocal() as db:
            result = db.execute(
                text("""
                    UPDATE users
                    SET email_verified_at = CURRENT_TIMESTAMP
                    WHERE id = :id AND email = :email
                """),
                {"id": registration.json()["id"], "email": email},
            )

            self.assertEqual(result.rowcount, 1)
            db.commit()

        login = self.client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": PASSWORD,
            },
        )

        self.assertEqual(
            login.status_code,
            200,
            login.text,
        )

        return {
            "id": registration.json()["id"],
            "token": login.json()["access_token"],
        }

    @staticmethod
    def auth_headers(user):
        return {
            "Authorization": f"Bearer {user['token']}"
        }

    def test_competency_assessment_persists(self):
        endpoint = (
            "/api/roadmaps/competency-assessments/"
            f"{CAREER_KEY}/{self.competency_key}"
        )

        response = self.client.put(
            endpoint,
            headers=self.auth_headers(self.user_a),
            json={
                "proficiency_level": "intermediate",
                "notes": "Practicing data pipelines.",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        # Read using a NEW client and database session.
        with TestClient(app) as fresh_client:
            read = fresh_client.get(
                f"/api/roadmaps/competency-assessments/{CAREER_KEY}",
                headers=self.auth_headers(self.user_a),
            )

        self.assertEqual(
            read.status_code,
            200,
            read.text,
        )

        assessments = read.json()["assessments"]

        self.assertEqual(len(assessments), 1)
        self.assertEqual(
            assessments[0]["proficiency_level"],
            "intermediate",
        )
        self.assertEqual(
            assessments[0]["notes"],
            "Practicing data pipelines.",
        )

        # Independently verify the committed SQL row.
        with SessionLocal() as db:
            record = db.get(
                UserCompetencyAssessment,
                (
                    self.user_a["id"],
                    self.career_id,
                    self.competency_key,
                ),
            )

            self.assertIsNotNone(record)

            self.assertEqual(
                record.proficiency_level,
                "intermediate",
            )

    def test_competency_assessments_are_user_isolated(self):
        endpoint = (
            "/api/roadmaps/competency-assessments/"
            f"{CAREER_KEY}/{self.competency_key}"
        )

        response_a = self.client.put(
            endpoint,
            headers=self.auth_headers(self.user_a),
            json={
                "proficiency_level": "advanced",
                "notes": "User A assessment",
            },
        )

        self.assertEqual(response_a.status_code, 200)

        # User B should not see User A's assessment.
        response_b = self.client.get(
            f"/api/roadmaps/competency-assessments/{CAREER_KEY}",
            headers=self.auth_headers(self.user_b),
        )

        self.assertEqual(response_b.status_code, 200)
        self.assertEqual(
            response_b.json()["assessments"],
            [],
        )

        # User B saves a different assessment.
        update_b = self.client.put(
            endpoint,
            headers=self.auth_headers(self.user_b),
            json={
                "proficiency_level": "beginner",
                "notes": "User B assessment",
            },
        )

        self.assertEqual(update_b.status_code, 200)

        with SessionLocal() as db:
            record_a = db.get(
                UserCompetencyAssessment,
                (
                    self.user_a["id"],
                    self.career_id,
                    self.competency_key,
                ),
            )

            record_b = db.get(
                UserCompetencyAssessment,
                (
                    self.user_b["id"],
                    self.career_id,
                    self.competency_key,
                ),
            )

            self.assertIsNotNone(record_a)
            self.assertIsNotNone(record_b)

            self.assertEqual(
                record_a.proficiency_level,
                "advanced",
            )
            self.assertEqual(
                record_b.proficiency_level,
                "beginner",
            )

    def test_learning_progress_persists(self):
        endpoint = (
            f"/api/roadmaps/learning-progress/"
            f"{CAREER_KEY}/{self.competency_key}"
        )

        response = self.client.put(
            endpoint,
            headers=self.auth_headers(self.user_a),
            json={"learned": True},
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        with TestClient(app) as fresh_client:
            read = fresh_client.get(
                f"/api/roadmaps/learning-progress/{CAREER_KEY}",
                headers=self.auth_headers(self.user_a),
            )

        self.assertEqual(
            read.status_code,
            200,
            read.text,
        )

        skills = read.json()["skills"]

        self.assertTrue(
            any(
                item["skill_key"] == self.competency_key
                and item["learned"] is True
                for item in skills
            )
        )

        with SessionLocal() as db:
            record = db.get(
                UserLearningProgress,
                (
                    self.user_a["id"],
                    self.career_id,
                    self.competency_key,
                ),
            )

            self.assertIsNotNone(record)
            self.assertTrue(record.learned)

    def test_learning_progress_is_user_isolated(self):
        endpoint = (
            f"/api/roadmaps/learning-progress/"
            f"{CAREER_KEY}/{self.competency_key}"
        )

        response_a = self.client.put(
            endpoint,
            headers=self.auth_headers(self.user_a),
            json={"learned": True},
        )

        response_b = self.client.put(
            endpoint,
            headers=self.auth_headers(self.user_b),
            json={"learned": False},
        )

        self.assertEqual(response_a.status_code, 200)
        self.assertEqual(response_b.status_code, 200)

        with SessionLocal() as db:
            record_a = db.get(
                UserLearningProgress,
                (
                    self.user_a["id"],
                    self.career_id,
                    self.competency_key,
                ),
            )

            record_b = db.get(
                UserLearningProgress,
                (
                    self.user_b["id"],
                    self.career_id,
                    self.competency_key,
                ),
            )

            self.assertIsNotNone(record_a)
            self.assertIsNotNone(record_b)

            self.assertTrue(record_a.learned)
            self.assertFalse(record_b.learned)
            
    
    def send_persistent_mentor_message(
        self,
        user,
        message,
        conversation_id=None,
        reply="Mocked AI career advice.",
    ):
        payload = {
            "message": message,
            "career_key": CAREER_KEY,
        }

        if conversation_id is not None:
            payload["conversation_id"] = conversation_id

        # Mock AI computation, not conversation storage.
        # PostgreSQL reads and writes remain real.
        with (
            patch(
                "src.backend.app.api.routes.ai_mentor."
                "resolve_explicit_career_change",
                return_value=None,
            ),
            patch(
                "src.backend.app.services."
                "assessment_mentor_service.analyze_competency_gaps",
                return_value={
                    "career_name": "Data Engineer",
                },
            ),
            patch(
                "src.backend.app.services."
                "assessment_mentor_service.build_mentor_context",
                return_value={
                    "career": "Data Engineer",
                },
            ),
            patch(
                "src.backend.app.services."
                "assessment_mentor_service.generate_mentor_response",
                new_callable=AsyncMock,
                return_value=reply,
            ) as llm,
        ):
            response = self.client.post(
                "/api/ai-mentor/chat/assessment/persistent",
                headers=self.auth_headers(user),
                json=payload,
            )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        llm.assert_awaited_once()

        return response.json(), llm

    def test_mentor_conversation_persists(self):
        question = "How do I become a Data Engineer?"
        answer = "Start with Python, SQL and data pipelines."

        result, _ = self.send_persistent_mentor_message(
            user=self.user_a,
            message=question,
            reply=answer,
        )

        conversation_id = result["conversation_id"]

        self.assertEqual(result["response"], answer)
        self.assertEqual(result["career_key"], CAREER_KEY)

        # A fresh API client reads committed history.
        with TestClient(app) as fresh_client:
            conversations = fresh_client.get(
                "/api/ai-mentor/conversations",
                headers=self.auth_headers(self.user_a),
            )

            messages = fresh_client.get(
                f"/api/ai-mentor/conversations/"
                f"{conversation_id}/messages",
                headers=self.auth_headers(self.user_a),
            )

        self.assertEqual(
            conversations.status_code,
            200,
            conversations.text,
        )

        self.assertTrue(
            any(
                item["id"] == conversation_id
                for item in conversations.json()
            )
        )

        self.assertEqual(
            messages.status_code,
            200,
            messages.text,
        )

        history = messages.json()

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], question)
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], answer)

        # Independently verify committed SQL records.
        with SessionLocal() as db:
            conversation = db.get(
                MentorConversation,
                conversation_id,
            )

            self.assertIsNotNone(conversation)
            self.assertEqual(
                conversation.user_id,
                self.user_a["id"],
            )

            stored_messages = db.scalars(
                select(MentorMessage).where(
                    MentorMessage.conversation_id
                    == conversation_id
                )
            ).all()

            self.assertEqual(len(stored_messages), 2)

    def test_mentor_conversation_is_user_isolated(self):
        result, _ = self.send_persistent_mentor_message(
            user=self.user_a,
            message="Help me study SQL.",
        )

        conversation_id = result["conversation_id"]

        # User B must not see User A's conversation.
        conversations_b = self.client.get(
            "/api/ai-mentor/conversations",
            headers=self.auth_headers(self.user_b),
        )

        self.assertEqual(
            conversations_b.status_code,
            200,
            conversations_b.text,
        )

        self.assertFalse(
            any(
                item["id"] == conversation_id
                for item in conversations_b.json()
            )
        )

        history_b = self.client.get(
            f"/api/ai-mentor/conversations/"
            f"{conversation_id}/messages",
            headers=self.auth_headers(self.user_b),
        )

        self.assertEqual(
            history_b.status_code,
            404,
            history_b.text,
        )

        # User B also must not append messages to
        # User A's conversation.
        with (
            patch(
                "src.backend.app.api.routes.ai_mentor."
                "resolve_explicit_career_change",
                return_value=None,
            ),
            patch(
                "src.backend.app.services."
                "assessment_mentor_service.generate_mentor_response",
                new_callable=AsyncMock,
            ) as llm,
        ):
            attempt = self.client.post(
                "/api/ai-mentor/chat/assessment/persistent",
                headers=self.auth_headers(self.user_b),
                json={
                    "message": "Unauthorized follow-up",
                    "career_key": CAREER_KEY,
                    "conversation_id": conversation_id,
                },
            )

        self.assertEqual(
            attempt.status_code,
            404,
            attempt.text,
        )

        llm.assert_not_awaited()

        with SessionLocal() as db:
            saved_messages = db.scalars(
                select(MentorMessage).where(
                    MentorMessage.conversation_id
                    == conversation_id
                )
            ).all()

            self.assertEqual(len(saved_messages), 2)

    def test_mentor_followup_restores_history(self):
        first, _ = self.send_persistent_mentor_message(
            user=self.user_a,
            message="I want to become a Data Engineer.",
            reply="Start with SQL and Python.",
        )

        conversation_id = first["conversation_id"]

        second, llm = self.send_persistent_mentor_message(
            user=self.user_a,
            message="What should I study first?",
            conversation_id=conversation_id,
            reply="Begin with SQL fundamentals.",
        )

        self.assertEqual(
            second["conversation_id"],
            conversation_id,
        )

        # The LLM should receive previous messages.
        sent_history = llm.await_args.kwargs["history"]

        self.assertEqual(len(sent_history), 2)
        self.assertEqual(
            sent_history[0]["content"],
            "I want to become a Data Engineer.",
        )
        self.assertEqual(
            sent_history[1]["content"],
            "Start with SQL and Python.",
        )

        # Follow-up messages should be committed too.
        with SessionLocal() as db:
            messages = db.scalars(
                select(MentorMessage).where(
                    MentorMessage.conversation_id
                    == conversation_id
                )
            ).all()

            self.assertEqual(len(messages), 4)

    
    def upload_test_cv(
        self,
        user,
        filename,
        file_bytes,
        content_type,
        form_user_id=None,
    ):
        return self.client.post(
            "/api/recommendations/upload",
            headers=self.auth_headers(user),
            data={
                "user_id": str(
                    form_user_id
                    if form_user_id is not None
                    else user["id"]
                ),
                "top_k": "3",
            },
            files={
                "file": (
                    filename,
                    file_bytes,
                    content_type,
                ),
            },
        )

    def test_real_docx_upload_and_recommendations(self):
        response = self.upload_test_cv(
            user=self.user_a,
            filename="integration_resume.docx",
            file_bytes=create_test_docx(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        result = response.json()

        self.assertIn("Python", result["extracted_skills"])
        self.assertIn("SQL", result["extracted_skills"])
        self.assertIn("Python", result["model_skills"])

        self.assertEqual(
            len(result["recommendations"]),
            3,
        )

        for recommendation in result["recommendations"]:
            self.assertIn("career_key", recommendation)
            self.assertIn("rank", recommendation)
            self.assertIn("score", recommendation)

        # Verify a committed row using a new session.
        with SessionLocal() as db:
            resume = db.scalar(
                select(Resume).where(
                    Resume.user_id == self.user_a["id"]
                )
            )

            self.assertIsNotNone(resume)
            self.assertEqual(
                resume.file_name,
                "integration_resume.docx",
            )
            self.assertEqual(resume.file_type, "docx")

            self.assertIn(
                "FastAPI",
                resume.extracted_text,
            )

            self.assertEqual(
                resume.analysis_result["recommendations"],
                result["recommendations"],
            )

            # Verify that recognized skills are associated
            # with the correct user in PostgreSQL.
            recorded_skills = db.scalars(
                select(Skill.name)
                .join(
                    UserSkill,
                    UserSkill.skill_id == Skill.id,
                )
                .where(
                    UserSkill.user_id == self.user_a["id"]
                )
            ).all()

            self.assertTrue(
                {"Python", "SQL"}.issubset(
                    set(recorded_skills)
                )
            )

    def test_real_pdf_upload_and_persistence(self):
        response = self.upload_test_cv(
            user=self.user_a,
            filename="integration_resume.pdf",
            file_bytes=create_test_pdf(),
            content_type="application/pdf",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        self.assertEqual(
            len(response.json()["recommendations"]),
            3,
        )

        with SessionLocal() as db:
            resume = db.scalar(
                select(Resume).where(
                    Resume.user_id == self.user_a["id"]
                )
            )

            self.assertIsNotNone(resume)
            self.assertEqual(resume.file_type, "pdf")
            self.assertIn("PostgreSQL", resume.extracted_text)

    def test_saved_cv_isolated_between_users(self):
        upload = self.upload_test_cv(
            user=self.user_a,
            filename="private_resume.docx",
            file_bytes=create_test_docx(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )

        self.assertEqual(
            upload.status_code,
            200,
            upload.text,
        )

        # Use a new API client to retrieve committed data.
        with TestClient(app) as fresh_client:
            own_resume = fresh_client.get(
                "/api/recommendations/resumes/latest",
                headers=self.auth_headers(self.user_a),
            )

            other_resume = fresh_client.get(
                "/api/recommendations/resumes/latest",
                headers=self.auth_headers(self.user_b),
            )

        self.assertEqual(
            own_resume.status_code,
            200,
            own_resume.text,
        )

        self.assertEqual(
            own_resume.json()["filename"],
            "private_resume.docx",
        )

        self.assertEqual(
            other_resume.status_code,
            200,
            other_resume.text,
        )

        self.assertIsNone(other_resume.json())

    def test_cross_user_cv_upload_is_forbidden(self):
        response = self.upload_test_cv(
            user=self.user_a,
            filename="unauthorized_resume.pdf",
            file_bytes=create_test_pdf(),
            content_type="application/pdf",
            form_user_id=self.user_b["id"],
        )

        self.assertEqual(
            response.status_code,
            403,
            response.text,
        )

        # A rejected upload must not create a Resume row.
        with SessionLocal() as db:
            resumes = db.scalars(
                select(Resume).where(
                    Resume.user_id.in_(
                        [
                            self.user_a["id"],
                            self.user_b["id"],
                        ]
                    )
                )
            ).all()

            self.assertEqual(resumes, [])

    def test_cv_to_competency_gap_and_roadmap(self):
        """
        End-to-end backend workflow:
        CV -> Random Forest -> PostgreSQL
        -> competency gaps -> learning roadmap.
        """

        upload = self.upload_test_cv(
            user=self.user_a,
            filename="roadmap_integration.docx",
            file_bytes=create_test_docx(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )

        self.assertEqual(
            upload.status_code,
            200,
            upload.text,
        )

        gaps = self.client.get(
            f"/api/skill-gaps/users/{self.user_a['id']}"
            f"/careers/{CAREER_KEY}",
            headers=self.auth_headers(self.user_a),
        )

        self.assertEqual(
            gaps.status_code,
            200,
            gaps.text,
        )

        gap_data = gaps.json()

        self.assertEqual(
            gap_data["user_id"],
            self.user_a["id"],
        )
        self.assertEqual(
            gap_data["career_key"],
            CAREER_KEY,
        )

        competencies = gap_data["competencies"]

        self.assertGreater(len(competencies), 0)

        keys = {
            item["competency_key"]
            for item in competencies
        }

        self.assertEqual(
            len(keys),
            len(competencies),
        )

        # At least one recorded CV skill should provide
        # evidence for a Data Engineer competency.
        self.assertTrue(
            any(
                item["status"] == "evidenced"
                for item in competencies
            ),
            "CV skills did not evidence any competency.",
        )

        roadmap = self.client.get(
            f"/api/roadmaps/users/{self.user_a['id']}"
            f"/careers/{CAREER_KEY}",
            headers=self.auth_headers(self.user_a),
        )

        self.assertEqual(
            roadmap.status_code,
            200,
            roadmap.text,
        )

        data = roadmap.json()

        self.assertEqual(data["career_key"], CAREER_KEY)
        self.assertEqual(data["user_id"], self.user_a["id"])

        steps = data["steps"]

        self.assertEqual(data["total_steps"], len(steps))
        self.assertGreater(len(steps), 0)

        for position, step in enumerate(steps, start=1):
            self.assertIn(step["competency_key"], keys)
            self.assertEqual(step["priority"], position)
            self.assertIn("next_action", step)
            self.assertIn("suggested_resources", step)

    def test_roadmap_focus_and_optional_choices(self):
        """
        Verify personalization survives the real
        API and competency-gap service.
        """

        base = self.client.get(
            f"/api/roadmaps/users/{self.user_a['id']}"
            f"/careers/{CAREER_KEY}",
            headers=self.auth_headers(self.user_a),
        )

        self.assertEqual(base.status_code, 200, base.text)

        steps = base.json()["steps"]

        self.assertGreaterEqual(
            len(steps),
            2,
            "Expected at least two pending competencies.",
        )

        focused = steps[0]["competency_key"]
        optional = steps[1]["competency_key"]

        response = self.client.get(
            f"/api/roadmaps/users/{self.user_a['id']}"
            f"/careers/{CAREER_KEY}",
            headers=self.auth_headers(self.user_a),
            params=[
                ("focus_competencies", focused),
                ("optional_competencies", optional),
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        data = response.json()

        self.assertEqual(
            data["learning_preferences"]["focus_competencies"],
            [focused],
        )

        self.assertEqual(
            data["learning_preferences"]["optional_competencies"],
            [optional],
        )

        by_key = {
            step["competency_key"]: step
            for step in data["steps"]
        }

        self.assertEqual(
            by_key[focused]["priority_group"],
            "focused",
        )

        self.assertEqual(
            by_key[optional]["priority_group"],
            "optional",
        )

        # The same competency cannot be both.
        invalid = self.client.get(
            f"/api/roadmaps/users/{self.user_a['id']}"
            f"/careers/{CAREER_KEY}",
            headers=self.auth_headers(self.user_a),
            params=[
                ("focus_competencies", focused),
                ("optional_competencies", focused),
            ],
        )

        self.assertEqual(
            invalid.status_code,
            400,
            invalid.text,
        )

    def test_gap_and_roadmap_reject_foreign_user(self):
        """
        User B cannot request User A's personalized
        competency information.
        """

        endpoints = [
            f"/api/skill-gaps/users/{self.user_a['id']}"
            f"/careers/{CAREER_KEY}",

            f"/api/roadmaps/users/{self.user_a['id']}"
            f"/careers/{CAREER_KEY}",
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(
                    endpoint,
                    headers=self.auth_headers(self.user_b),
                )

                self.assertEqual(
                    response.status_code,
                    403,
                    response.text,
                )


    @unittest.skipUnless(
        os.getenv("CAREERFORGE_RUN_LIVE_LLM") == "1",
        "Live Ollama integration test is disabled.",
    )
    def test_live_ollama_persistent_mentor(self):
        """
        Real end-to-end AI Mentor integration.

        No mocked AI responses.

        Flow:
        CV upload -> competency analysis -> Ollama
        -> PostgreSQL -> follow-up -> saved history.
        """

        from time import perf_counter

        # 1. Upload a real DOCX CV.
        upload = self.upload_test_cv(
            user=self.user_a,
            filename="live_mentor_cv.docx",
            file_bytes=create_test_docx(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )

        self.assertEqual(
            upload.status_code,
            200,
            upload.text,
        )

        headers = self.auth_headers(self.user_a)

        endpoint = (
            "/api/ai-mentor/chat/assessment/persistent"
        )

        first_question = (
            "Based on my CV and current skills, "
            "recommend two things I should focus on "
            "for a Data Engineer career. "
            "Keep your answer concise."
        )

        # 2. Call the REAL Ollama model.
        started = perf_counter()

        first = self.client.post(
            endpoint,
            headers=headers,
            json={
                "message": first_question,
                "career_key": CAREER_KEY,
            },
        )

        first_duration = perf_counter() - started

        self.assertEqual(
            first.status_code,
            200,
            first.text,
        )

        first_result = first.json()

        conversation_id = first_result["conversation_id"]
        first_answer = first_result["response"]

        self.assertIsInstance(conversation_id, int)
        self.assertGreater(len(first_answer.strip()), 20)

        self.assertEqual(
            first_result["career_key"],
            CAREER_KEY,
        )

        print("\n========== LIVE MENTOR RESPONSE ==========")
        print(f"Conversation ID: {conversation_id}")
        print(f"Duration: {first_duration:.2f}s")
        print(f"Response:\n{first_answer}")

        # 3. Send a follow-up using the SAME conversation.
        second_question = (
            "Which of those two should I tackle first, "
            "and why? Keep your answer concise."
        )

        started = perf_counter()

        second = self.client.post(
            endpoint,
            headers=headers,
            json={
                "message": second_question,
                "career_key": CAREER_KEY,
                "conversation_id": conversation_id,
            },
        )

        second_duration = perf_counter() - started

        self.assertEqual(
            second.status_code,
            200,
            second.text,
        )

        second_result = second.json()

        self.assertEqual(
            second_result["conversation_id"],
            conversation_id,
        )

        self.assertGreater(
            len(second_result["response"].strip()),
            20,
        )

        print("\n========== LIVE FOLLOW-UP ==========")
        print(f"Duration: {second_duration:.2f}s")
        print(second_result["response"])

        # 4. Read committed messages using a new API client.
        with TestClient(app) as fresh_client:
            history_response = fresh_client.get(
                (
                    "/api/ai-mentor/conversations/"
                    f"{conversation_id}/messages"
                ),
                headers=headers,
            )

        self.assertEqual(
            history_response.status_code,
            200,
            history_response.text,
        )

        history = history_response.json()

        self.assertEqual(len(history), 4)

        self.assertEqual(
            [item["role"] for item in history],
            ["user", "assistant", "user", "assistant"],
        )

        self.assertEqual(
            history[0]["content"],
            first_question,
        )

        self.assertEqual(
            history[1]["content"],
            first_answer,
        )

        self.assertEqual(
            history[2]["content"],
            second_question,
        )

        self.assertEqual(
            history[3]["content"],
            second_result["response"],
        )

        print("\n========== LIVE OLLAMA INTEGRATION ==========")
        print("Real Ollama inference: PASS")
        print("Follow-up conversation: PASS")
        print("Committed message persistence: PASS")
        print("Stored messages: 4")
        print("Database: careerforge_test")



if __name__ == "__main__":
    unittest.main()
