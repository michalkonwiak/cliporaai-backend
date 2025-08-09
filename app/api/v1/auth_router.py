from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def _current_user(
    token: str = Security(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    service = AuthService(db)
    return await service.get_current_user(token)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    """
    Register a new user
    """
    service = AuthService(db)
    return await service.register(user_in)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    service = AuthService(db)
    user = await service.authenticate(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await service.create_token(user)


@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(_current_user)) -> UserRead:
    """
    Get current user information
    """
    return current_user
