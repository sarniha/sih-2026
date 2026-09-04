from typing import Optional
import secrets

from fastapi import Header, HTTPException, status

from app.core.config import settings


def verify_service_token(x_service_token: Optional[str] = Header(default=None)) -> None:
    """Gate ingestion/write endpoints behind a shared service token.

    Not OAuth2/JWT by design — a single static token compared in constant
    time, per the project's deliberately lightweight auth decision.
    """
    if not settings.service_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="service_token is not configured on the server.",
        )

    if not x_service_token or not secrets.compare_digest(x_service_token, settings.service_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing service token",
        )