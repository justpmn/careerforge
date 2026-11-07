
import unittest

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt

from src.backend.app.core import tokens


TEST_SECRET = (
    "careerforge-test-only-secret-key-"
    "minimum-32-bytes"
)

USER_ID = 101


class TestJWTTokens(unittest.TestCase):

    def setUp(self):
        # Never depend on the actual development secret.
        secret_patch = patch.object(
            tokens,
            "get_jwt_secret",
            return_value=TEST_SECRET,
        )

        secret_patch.start()
        self.addCleanup(secret_patch.stop)

    def make_token(
        self,
        overrides=None,
        excluded=(),
        secret=TEST_SECRET,
        algorithm="HS256",
    ):
        now = datetime.now(timezone.utc)

        payload = {
            "sub": str(USER_ID),
            "iss": tokens.JWT_ISSUER,
            "aud": tokens.JWT_AUDIENCE,
            "iat": now,
            "exp": now + timedelta(minutes=10),
            "token_type": "access",
        }

        if overrides:
            payload.update(overrides)

        for claim in excluded:
            payload.pop(claim, None)

        return jwt.encode(
            payload,
            secret,
            algorithm=algorithm,
        )

    def assert_token_rejected(self, token):
        with self.assertRaises(ValueError):
            tokens.decode_access_token(token)

    def test_valid_token_is_accepted(self):
        token = tokens.create_access_token(
            user_id=USER_ID
        )

        result = tokens.decode_access_token(token)

        self.assertEqual(result, USER_ID)

    def test_expired_token_is_rejected(self):
        token = tokens.create_access_token(
            user_id=USER_ID,
            expires_delta=timedelta(seconds=-60),
        )

        self.assert_token_rejected(token)

    def test_tampered_signature_is_rejected(self):
        token = self.make_token()

        header, payload, signature = token.split(".")

        replacement = (
            "A" if signature[0] != "A" else "B"
        )

        tampered_signature = (
            replacement + signature[1:]
        )

        tampered_token = (
            f"{header}.{payload}.{tampered_signature}"
        )

        self.assert_token_rejected(tampered_token)

    def test_wrong_signing_secret_is_rejected(self):
        token = self.make_token(
            secret="another-secret-key-for-testing-only"
        )

        self.assert_token_rejected(token)

    def test_wrong_issuer_is_rejected(self):
        token = self.make_token(
            overrides={"iss": "unknown-issuer"}
        )

        self.assert_token_rejected(token)

    def test_wrong_audience_is_rejected(self):
        token = self.make_token(
            overrides={"aud": "different-api"}
        )

        self.assert_token_rejected(token)

    def test_missing_required_claims_are_rejected(self):
        required_claims = (
            "sub",
            "iss",
            "aud",
            "iat",
            "exp",
            "token_type",
        )

        for claim in required_claims:
            with self.subTest(claim=claim):
                token = self.make_token(
                    excluded=(claim,)
                )

                self.assert_token_rejected(token)

    def test_wrong_token_type_is_rejected(self):
        token = self.make_token(
            overrides={"token_type": "refresh"}
        )

        self.assert_token_rejected(token)

    def test_invalid_subjects_are_rejected(self):
        invalid_subjects = (
            "0",
            "-1",
            "abc",
            "00101",
            "",
            101,
        )

        for subject in invalid_subjects:
            with self.subTest(subject=subject):
                token = self.make_token(
                    overrides={"sub": subject}
                )

                self.assert_token_rejected(token)

    def test_wrong_algorithm_is_rejected(self):
        token = self.make_token(
            algorithm="HS384"
        )

        self.assert_token_rejected(token)

    def test_future_issued_at_is_rejected(self):
        future = (
            datetime.now(timezone.utc)
            + timedelta(hours=1)
        )

        token = self.make_token(
            overrides={"iat": future}
        )

        self.assert_token_rejected(token)

    def test_malformed_token_is_rejected(self):
        self.assert_token_rejected(
            "not-a-valid-jwt"
        )

    def test_invalid_user_ids_cannot_create_tokens(self):
        for user_id in (0, -1, True, "101", None):
            with self.subTest(user_id=user_id):
                with self.assertRaises(ValueError):
                    tokens.create_access_token(
                        user_id=user_id
                    )


if __name__ == "__main__":
    unittest.main()
