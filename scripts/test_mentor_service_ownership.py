
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from src.backend.app.services.mentor_conversation_service import (
    get_owned_conversation,
    get_recent_mentor_history,
    list_owned_mentor_conversations,
    list_owned_mentor_messages,
    save_mentor_message,
)
from src.backend.app.services.assessment_mentor_service import (
    generate_persistent_assessment_mentor_response,
)


USER_A = 101
FOREIGN_CONVERSATION = 555


class TestMentorServiceOwnership(
    unittest.IsolatedAsyncioTestCase
):

    def setUp(self):
        self.db = MagicMock()

    def test_conversation_lookup_requires_owner(self):
        self.db.scalar.return_value = None

        with self.assertRaises(ValueError):
            get_owned_conversation(
                db=self.db,
                user_id=USER_A,
                conversation_id=FOREIGN_CONVERSATION,
            )

        statement = self.db.scalar.call_args.args[0]
        params = list(statement.compile().params.values())

        self.assertIn(USER_A, params)
        self.assertIn(FOREIGN_CONVERSATION, params)

    def test_foreign_conversation_history_is_blocked(self):
        self.db.scalar.return_value = None

        with self.assertRaises(ValueError):
            get_recent_mentor_history(
                db=self.db,
                user_id=USER_A,
                conversation_id=FOREIGN_CONVERSATION,
            )

        with self.assertRaises(ValueError):
            list_owned_mentor_messages(
                db=self.db,
                user_id=USER_A,
                conversation_id=FOREIGN_CONVERSATION,
            )

        self.db.scalars.assert_not_called()

    def test_foreign_conversation_cannot_receive_messages(self):
        self.db.scalar.return_value = None

        with self.assertRaises(ValueError):
            save_mentor_message(
                db=self.db,
                user_id=USER_A,
                conversation_id=FOREIGN_CONVERSATION,
                role="user",
                content="Unauthorized message",
            )

        self.db.add.assert_not_called()
        self.db.flush.assert_not_called()

    def test_conversation_listing_is_user_scoped(self):
        self.db.scalars.return_value.all.return_value = []

        result = list_owned_mentor_conversations(
            db=self.db,
            user_id=USER_A,
        )

        self.assertEqual(result, [])

        statement = self.db.scalars.call_args.args[0]
        params = list(statement.compile().params.values())

        self.assertIn(USER_A, params)

    async def test_persistent_chat_rejects_foreign_conversation(self):
        # First scalar: resolve career ID.
        # Second scalar: look up conversation owned by USER_A.
        self.db.scalar.side_effect = [77, None]

        with (
            patch(
                "src.backend.app.services."
                "assessment_mentor_service.generate_mentor_response",
                new_callable=AsyncMock,
            ) as llm,
            patch(
                "src.backend.app.services."
                "assessment_mentor_service.analyze_competency_gaps"
            ) as assessment,
        ):
            with self.assertRaises(ValueError):
                await generate_persistent_assessment_mentor_response(
                    db=self.db,
                    user_id=USER_A,
                    career_key="data_engineer",
                    message="Help with SQL",
                    conversation_id=FOREIGN_CONVERSATION,
                )

        ownership_query = (
            self.db.scalar.call_args_list[1].args[0]
        )
        params = list(
            ownership_query.compile().params.values()
        )

        self.assertIn(USER_A, params)
        self.assertIn(FOREIGN_CONVERSATION, params)

        llm.assert_not_awaited()
        assessment.assert_not_called()
        self.db.add.assert_not_called()


if __name__ == "__main__":
    unittest.main()
