from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import create_access_token, verify_access_token
from app.db.models import User
from app.db.session import get_db
from app.modules.auth.schemas import CreateUserRequest, LoginRequest, TokenResponse, UserPublic
from app.modules.auth.service import authenticate_user, create_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
router = APIRouter(prefix="/api", tags=["authentication"])


def user_public(user: User) -> UserPublic:
    return UserPublic(id=user.id, username=user.username, role=user.role, is_active=user.is_active)  # type: ignore[arg-type]


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    try:
        claims = verify_access_token(token, settings)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    user = db.get(User, claims.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号不可用")
    return user


def require_roles(*roles: str) -> Callable:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有执行此操作的权限")
        return current_user

    return dependency


@router.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> TokenResponse:
    user = authenticate_user(db, request.username, request.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    return TokenResponse(access_token=create_access_token(user.id, user.role, settings), user=user_public(user))


@router.get("/auth/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return user_public(current_user)


@router.post("/users", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def add_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> UserPublic:
    try:
        return user_public(create_user(db, request.username, request.password, request.role))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
