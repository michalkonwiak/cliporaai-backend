import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import TokenExpiredError, credentials_exception

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = str(settings.secret_key.get_secret_value() if settings.secret_key else "")
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
JWT_LEEWAY_SECONDS = settings.jwt_leeway_seconds
JWT_ISSUER = settings.jwt_issuer
JWT_AUDIENCE = settings.jwt_audience

# In-memory key store for asymmetric algorithms
_JWT_PRIVATE_KEYS: dict[str, str] = {}
_JWT_PUBLIC_KEYS: dict[str, str] = {}


def load_jwt_keys() -> None:
    """Load asymmetric JWT keys into memory based on settings.
    Supports a single key pair for now, optionally tagged with settings.jwt_kid.
    """
    global _JWT_PRIVATE_KEYS, _JWT_PUBLIC_KEYS
    if ALGORITHM not in ("RS256", "ES256"):
        return
    if not settings.jwt_private_key_path or not settings.jwt_public_key_path:
        logger.warning("Asymmetric algorithm configured but key paths are not set")
        return
    try:
        kid = settings.jwt_kid or "default"
        priv = Path(settings.jwt_private_key_path).read_text()
        pub = Path(settings.jwt_public_key_path).read_text()
        _JWT_PRIVATE_KEYS = {kid: priv}
        _JWT_PUBLIC_KEYS = {kid: pub}
        logger.info(f"Loaded JWT keys for kid='{kid}'")
    except Exception as e:
        logger.error(f"Failed to load JWT keys: {e}")
        if settings.environment == "production":
            # Fail fast in production
            raise


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return str(pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bool(pwd_context.verify(plain_password, hashed_password))


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """
    Create a new JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        # Add issued at claim for additional security
        "iat": datetime.utcnow(),
        # Add issuer and audience claims
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE
    })
    headers: dict[str, Any] = {}
    if settings.jwt_kid:
        headers["kid"] = settings.jwt_kid
    if ALGORITHM in ("RS256", "ES256"):
        kid = settings.jwt_kid or next(iter(_JWT_PRIVATE_KEYS.keys()), None)
        private_key = _JWT_PRIVATE_KEYS.get(kid) if kid else None
        if not private_key:
            logger.error("No JWT private key loaded for signing")
            raise RuntimeError("JWT private key not loaded")
        return str(jwt.encode(to_encode, private_key, algorithm=ALGORITHM, headers=headers or None))
    return str(jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM, headers=headers or None))


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: The JWT token to decode
        
    Returns:
        The decoded token payload
        
    Raises:
        credentials_exception: If the token is invalid
        TokenExpiredError: If the token has expired
    """
    try:
        header = jwt.get_unverified_header(token)
        
        if ALGORITHM in ("RS256", "ES256"):
            kid = header.get("kid")
            key: str | None = None
            if kid and kid in _JWT_PUBLIC_KEYS:
                key = _JWT_PUBLIC_KEYS[kid]
            elif not kid and len(_JWT_PUBLIC_KEYS) == 1:
                key = next(iter(_JWT_PUBLIC_KEYS.values()))
            elif kid and kid not in _JWT_PUBLIC_KEYS:
                logger.warning(f"JWT kid '{kid}' not found in key store")
            if not key:
                logger.warning("No suitable JWT public key found for verification")
                raise credentials_exception
        else:
            key = SECRET_KEY
        
        payload = jwt.decode(
            token,
            key,
            algorithms=[ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "require_exp": True,
                "verify_iss": True,
                "verify_aud": True,
                "leeway": JWT_LEEWAY_SECONDS,
            },
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
        )
        
        if "sub" not in payload:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception
            
        return dict(payload)
    except ExpiredSignatureError:
        logger.info("Token has expired")
        raise TokenExpiredError("Token has expired") from None
    except (JWTError, ValidationError) as e:
        logger.warning(f"Token validation failed: {str(e)}")
        raise credentials_exception from None
