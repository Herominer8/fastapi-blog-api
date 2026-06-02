from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional

# User
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime
    profile_picture: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Post
class PostCreate(BaseModel):
    title: str
    content: str
    is_published: Optional[bool] = False

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None

class PostOut(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    is_published: bool
    likes_count: Optional[int] = 0
    comments_count: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)

# Comment
class CommentCreate(BaseModel):
    content: str
    post_id: int

class CommentOut(BaseModel):
    id: int
    content: str
    user_id: int
    post_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Token & Refresh
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class Message(BaseModel):
    message: str
    success: bool = True



class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


#Verify Email
class VerifyEmailRequest(BaseModel):
    code: str


class ProfilePictureResponse(BaseModel):
    message: str
    file_path: str