
from authlib.integrations.starlette_client import OAuth

from src.backend.app.core.config import settings


oauth = OAuth()

oauth.register(
    name="github",
    client_id=settings.github_oauth_client_id,
    client_secret=settings.github_oauth_client_secret,
    authorize_url="https://github.com/login/oauth/authorize",
    access_token_url="https://github.com/login/oauth/access_token",
    api_base_url="https://api.github.com/",
    client_kwargs={
        "scope": "user:email",
        "code_challenge_method": "S256",
    },
)

oauth.register(
    name="google",
    client_id=settings.google_oauth_client_id,
    client_secret=settings.google_oauth_client_secret,
    server_metadata_url=(
        "https://accounts.google.com/"
        ".well-known/openid-configuration"
    ),
    client_kwargs={
        "scope": "openid email profile",
        "code_challenge_method": "S256",
    },
)
