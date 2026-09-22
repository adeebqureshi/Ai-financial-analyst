from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.dependencies import get_auth_db, get_auth_settings
from app.auth.dependencies import get_current_user
from app.auth.exceptions import AuthenticationError
from app.auth.models import User
from app.auth.schemas import Token, UserCreate, UserOut
from app.auth.security import create_access_token
from app.auth.service import UserService
from app.core.config import Settings
from app.schemas.base import APIResponse
router = APIRouter(prefix="/auth", tags=["Auth"])
@router.post(
    "/register",
    response_model=APIResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
    description="Creates a user account with a securely hashed password.",
)
def register(
    payload: UserCreate,
    session=Depends(get_auth_db),
) -> APIResponse[UserOut]:
    user = UserService(session).register(payload.email, payload.password)
    return APIResponse.success_response(
        message="Account created",
        data=UserOut(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )
@router.post(
    "/token",
    response_model=Token,
    summary="Obtain an access token",
    description=(
        "Exchanges email/password credentials for a signed JWT bearer token "
        "(standard OAuth2 password flow)."
    ),
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    settings: Settings = Depends(get_auth_settings),
    session=Depends(get_auth_db),
) -> Token:
    user = UserService(session).authenticate(form_data.username, form_data.password)
    if user is None:
        raise AuthenticationError("Incorrect email or password.")
    token = create_access_token(
        subject=user.id,
        secret_key=settings.auth_secret_key_str,
        expires_minutes=settings.access_token_expire_minutes,
    )
    return Token(access_token=token)
@router.get(
    "/me",
    response_model=APIResponse[UserOut],
    summary="Current user profile",
    description="Returns the profile of the authenticated caller.",
)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserOut]:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )
    return APIResponse.success_response(
        message="Authenticated user",
        data=UserOut(
            id=current_user.id,
            email=current_user.email,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
        ),
    )