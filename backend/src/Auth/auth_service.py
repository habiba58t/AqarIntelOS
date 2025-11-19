from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from . import auth_models, auth_utils, auth_schemas
from fastapi import HTTPException, status
import uuid

class AuthService:
    @staticmethod
    # async def register_user(db: AsyncSession, user_data: auth_schemas.UserCreate):
    #     # Check if user already exists
    #     result = await db.execute(
    #         select(auth_models.User).where(auth_models.User.email == user_data.email)
    #     )
    #     existing_user = result.scalar_one_or_none()
        
    #     if existing_user:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="Email already registered"
    #         )
        
    #     # Create new user
    #     hashed_password = auth_utils.get_password_hash(user_data.password)
    #     db_user = auth_models.User(
    #         email=user_data.email,
    #         name=user_data.name,
    #         password_hash=hashed_password
    #     )
        
    #     db.add(db_user)
    #     await db.commit()
    #     await db.refresh(db_user)
        
    #     return db_user
    async def register_user(db: AsyncSession, user_data: auth_schemas.UserCreate):
        # Check if user already exists
        result = await db.execute(
            select(auth_models.User).where(auth_models.User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Generate thread_id for the new user
        thread_id = str(uuid.uuid4())
        print(f"🆕 Creating user with thread_id: {thread_id}")
        
        # Create new user with thread_id
        hashed_password = auth_utils.get_password_hash(user_data.password)
        db_user = auth_models.User(
            email=user_data.email,
            name=user_data.name,
            password_hash=hashed_password,
            thread_id=thread_id  # ✅ Set thread_id here
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        return db_user


    @staticmethod
    # async def authenticate_user(db: AsyncSession, email: str, password: str):
    #     result = await db.execute(
    #         select(auth_models.User).where(
    #             auth_models.User.email == email,
    #             auth_models.User.is_active == True
    #         )
    #     )
    #     user = result.scalar_one_or_none()
        
    #     if not user or not auth_utils.verify_password(password, user.password_hash):
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Invalid email or password"
    #         )
        
    #     return user
    async def authenticate_user(db: AsyncSession, email: str, password: str):
        result = await db.execute(
            select(auth_models.User).where(
                auth_models.User.email == email,
                auth_models.User.is_active == True
            )
        )
        user = result.scalar_one_or_none()
        
        if not user or not auth_utils.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        return user

    @staticmethod
    async def get_current_user(db: AsyncSession, token: str):
        payload = auth_utils.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        result = await db.execute(
            select(auth_models.User).where(
                auth_models.User.id == uuid.UUID(user_id),
                auth_models.User.is_active == True
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user