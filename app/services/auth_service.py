from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from app.models import User, UserRole
from app.schemas import UserCreate
from app.config import settings
from app.services.color_service import generate_color_for_user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user (case-insensitive username)"""
    user = db.query(User).filter(User.username.ilike(username)).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(user_data.password)
    
    # Create user (need to commit to get the ID)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=UserRole.TRAVELLER
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Assign permanent heatmap color based on user ID and username
    db_user.heatmap_color = generate_color_for_user(db_user.id, db_user.username)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def update_user_xp(db: Session, user: User, xp_gain: int) -> User:
    """Update user XP and handle level-ups"""
    user.xp += xp_gain
    
    # Simple level calculation: 100 XP per level
    new_level = (user.xp // 100) + 1
    if new_level > user.level:
        user.level = new_level
    
    db.commit()
    db.refresh(user)
    return user
