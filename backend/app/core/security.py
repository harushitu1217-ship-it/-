from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import Settings

PASSWORD_HASHER = PasswordHasher()


@dataclass(frozen=True)
class TokenClaims:
    user_id: str
    role: str


def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("密码至少需要 10 个字符")
    return PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(
    user_id: str,
    role: str,
    settings: Settings,
    *,
    expires_delta: timedelta = timedelta(hours=8),
) -> str:
    expires_at = datetime.now(UTC) + expires_delta
    return jwt.encode({"sub": user_id, "role": role, "exp": expires_at}, settings.jwt_secret, algorithm="HS256")


def verify_access_token(token: str, settings: Settings) -> TokenClaims:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("登录已过期，请重新登录") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError("登录凭证无效") from exc
    user_id = str(payload.get("sub", ""))
    role = str(payload.get("role", ""))
    if not user_id or role not in {"admin", "operator", "reviewer"}:
        raise ValueError("登录凭证无效")
    return TokenClaims(user_id=user_id, role=role)
