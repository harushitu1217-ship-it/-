from datetime import timedelta

import pytest

from app.core.config import Settings
from app.core.security import create_access_token, hash_password, verify_access_token, verify_password


def test_password_hash_round_trip():
    password_hash = hash_password("StrongPass123!")

    assert password_hash != "StrongPass123!"
    assert verify_password("StrongPass123!", password_hash)
    assert not verify_password("wrong", password_hash)


def test_access_token_preserves_user_and_role():
    settings = Settings(jwt_secret="test-secret")

    token = create_access_token("user-1", "reviewer", settings, expires_delta=timedelta(minutes=5))

    claims = verify_access_token(token, settings)
    assert claims.user_id == "user-1"
    assert claims.role == "reviewer"


def test_expired_access_token_is_rejected():
    settings = Settings(jwt_secret="test-secret")
    token = create_access_token("user-1", "operator", settings, expires_delta=timedelta(seconds=-1))

    with pytest.raises(ValueError, match="登录已过期"):
        verify_access_token(token, settings)
