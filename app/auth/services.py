from datetime import UTC, datetime, timedelta
import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from app.user.models import UserStatus
from ..core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from ..user.schema import UserResponse
from ..core.exceptions import UnauthorizedError
from uuid import uuid4
from ..auth.schema import Token, TokenPayload
from ..db.redis import revoke_token, is_token_revoked
from pydantic import ValidationError

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class AuthenticationService:
    def __init__(self, db: AsyncSession):
        from ..user.services import UserService
        from ..user.repository import UserRepository
        self.db = db
        self.user_service = UserService(db)
        self.user_repo = UserRepository(db)

    @staticmethod
    def hash_password(password: str) -> str:
        return password_hash.hash(password)
    
    @staticmethod
    def verify_password(password: str | None, hashed_password: str | None) -> bool:
        if hashed_password is None:
            return password is None
        
        if password is None:
            return False

        return password_hash.verify(password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, refresh: bool = False) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()

        expire = datetime.now(UTC) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES if refresh else settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        to_encode.update({"exp": expire, "refresh": refresh, "jti": str(uuid4())})

        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY.get_secret_value(),
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    async def verify_token(token: str, refresh: bool = False) -> TokenPayload | None:
        """Verify a JWT access token"""
        try:
            logging.info(f"verifying {'refresh' if refresh else 'access'} token")
            # payload["refresh"] False if token sent is an access token, True if token sent is a refresh token
            payload = jwt.decode(
                token,
                settings.SECRET_KEY.get_secret_value(),
                algorithms=[settings.ALGORITHM],
                options={"require": ["exp", "sub", "jti", "refresh", "user_code", "user_type"]}
            )

            payload = TokenPayload(**payload)

            if payload.refresh != refresh:
                detail = f"Please provide {'an access' if not refresh else 'a refresh'} token"
                raise UnauthorizedError(detail=detail)

            if await is_token_revoked(payload.jti):
                raise UnauthorizedError(detail="Token has been revoked")

            return payload
        
        except (jwt.InvalidTokenError, ValidationError):
            logging.error(f"Invalid token")
            return None
        
    def build_token_pair(self, user: UserResponse) -> Token:
        """Build a token pair for a user"""
        data = {
            "sub": str(user.id), 
            "user_code": user.user_code, 
            "user_type": user.user_type.value
        }
        access_token = self.create_access_token(data=data, refresh=False)
        refresh_token = self.create_access_token(data=data, refresh=True)
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
        
    async def user_from_token(self, token: str, refresh: bool = False) -> UserResponse:
        """Get the current authenticated user"""

        payload = await self.verify_token(token, refresh)
        
        if not payload:
            raise UnauthorizedError(detail="Invalid or expired token")
            
        return await self.user_service.get_user_by_user_code(payload.user_code, UserStatus.ACTIVE)
    
    async def login_user_by_user_code(self, user_code: str, password: str | None) -> Token:
        """Login a user by email"""
        user_code = user_code.strip().upper()
        user = await self.user_repo.get_user_by_user_code(user_code)
        if not user or not self.verify_password(password, user.password_hash):
            raise UnauthorizedError(detail="Invalid credentials")

        if user.status != UserStatus.ACTIVE:
            raise UnauthorizedError(detail=f"User is {user.status.value.lower()} and cannot login. Please contact support.")
        
        return self.build_token_pair(UserResponse.model_validate(user))
        

    async def refresh_token(self, token: str, user: UserResponse) -> Token:
        """Refresh a token"""
        payload = await self.verify_token(token, refresh=True)
        if not payload:
            raise UnauthorizedError(detail="Invalid or expired token")
        
        if payload.user_code != user.user_code:
            raise UnauthorizedError(detail="Invalid user")

        await revoke_token(payload.jti, payload.exp)

        return self.build_token_pair(user)
    

    async def logout(self, token: str) -> None:
        """Logout a user by revoking their token"""
        payload = await self.verify_token(token, refresh=False)
        if not payload:
            raise UnauthorizedError(detail="Invalid or expired token")
        
        await revoke_token(payload.jti, payload.exp)