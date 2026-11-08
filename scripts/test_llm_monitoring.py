import unittest
from unittest.mock import patch
import httpx
from src.backend.app.services.llm_monitoring import (monitor_mentor_inference)

class TestLLMMonitoring(
    unittest.IsolatedAsyncioTestCase
):

    async def test_successful_inference_is_logged(self):
        events = []

        @monitor_mentor_inference
        async def fake_mentor(message: str) -> str:
            return "Career advice generated."

        with patch(
            "src.backend.app.services.llm_monitoring.record_system_event",
            side_effect=lambda **kwargs: events.append(kwargs),
        ):
            result = await fake_mentor("Help me with cloud.")

        self.assertEqual(
            result,
            "Career advice generated.",
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0]["action"],
            "mentor_inference_completed",
        )
        self.assertEqual(
            events[0]["severity"],
            "INFO",
        )
        self.assertGreaterEqual(
            events[0]["duration_ms"],
            0,
        )

    async def test_timeout_is_logged(self):
        events = []

        @monitor_mentor_inference
        async def fake_mentor():
            try:
                raise httpx.ReadTimeout(
                    "Test timeout"
                )
            except httpx.ReadTimeout as error:
                raise RuntimeError(
                    "Ollama response timed out."
                ) from error

        with patch(
            "src.backend.app.services.llm_monitoring.record_system_event",
            side_effect=lambda **kwargs: events.append(kwargs),
        ):
            with self.assertRaises(RuntimeError):
                await fake_mentor()

        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0]["action"],
            "mentor_inference_timeout",
        )

    async def test_connection_failure_is_logged(self):
        events = []

        @monitor_mentor_inference
        async def fake_mentor():
            try:
                raise httpx.ConnectError(
                    "Connection refused"
                )
            except httpx.ConnectError as error:
                raise RuntimeError(
                    "Could not communicate with Ollama."
                ) from error

        with patch(
            "src.backend.app.services.llm_monitoring.record_system_event",
            side_effect=lambda **kwargs: events.append(kwargs),
        ):
            with self.assertRaises(RuntimeError):
                await fake_mentor()

        self.assertEqual(
            events[0]["action"],
            "mentor_connection_failed",
        )

    async def test_logging_failure_does_not_break_mentor(self):
        @monitor_mentor_inference
        async def fake_mentor():
            return "Working response"

        with patch(
            "src.backend.app.services.llm_monitoring.record_system_event",
            side_effect=OSError("Log unavailable"),
        ):
            with patch(
                "src.backend.app.services.llm_monitoring.logger"
            ):
                result = await fake_mentor()

        self.assertEqual(
            result,
            "Working response",
        )

    async def test_real_mentor_function_returns_text(self):
        from src.backend.app.services.llm_service import (
            generate_mentor_response,
        )

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "message": {
                        "content": "Mocked career advice"
                    }
                }

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def post(self, *args, **kwargs):
                return FakeResponse()

        with (
            patch(
                "src.backend.app.services.llm_service.httpx.AsyncClient",
                return_value=FakeClient(),
            ),
            patch(
                "src.backend.app.services.llm_service.build_mentor_messages",
                return_value=[
                    {"role": "user", "content": "Hello"}
                ],
            ),
            patch(
                "src.backend.app.services.llm_monitoring.record_system_event"
            ),
        ):
            result = await generate_mentor_response("Hello")

        self.assertEqual(result, "Mocked career advice")
        
if __name__ == "__main__":
    unittest.main()

