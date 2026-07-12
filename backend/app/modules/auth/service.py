from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db.models import User


def create_user(db: Session, username: str, password: str, role: str) -> User:
    normalized = username.strip().lower()
    if db.scalar(select(User).where(User.username == normalized)):
        raise ValueError("账号已存在")
    user = User(username=normalized, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username.strip().lower()))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user
