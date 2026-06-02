from fastapi import FastAPI, Depends, HTTPException, status, Query, Request, BackgroundTasks, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from typing import List
from app.core.database import engine, Base, get_db
from app.models import User, Post, Like, Comment, Notification
from app.websocket_manager import manager
from app.schemas import *
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token, verify_token_type, setup_cors
from app.core.dependencies import get_current_user, get_current_user_optional, require_admin, require_verified_user
import secrets
from datetime import datetime, timedelta, timezone
import time
import os
import shutil
from uuid import uuid4
import asyncio
# from app.core.email import send_reset_email


UPLOAD_DIR = "uploads/profile_pictures"
os.makedirs(UPLOAD_DIR, exist_ok=True)


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="RESTful Blog API", version="1.0.0")
app.state.limiter = limiter 
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
setup_cors(app)
Base.metadata.create_all(bind=engine, checkfirst=True)

# ========== AUTH ==========
@app.post("/register", response_model=UserOut)
@limiter.limit("3/minute")
def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == user.username) | (User.email == user.email)).first():
        raise HTTPException(400, "Username or email already exists")
    hashed = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
@limiter.limit("15/minute")
def login(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    
    if db_user and db_user.locked_until and db_user.locked_until > datetime.now(timezone.utc):
        remaining = (db_user.locked_until - datetime.now(timezone.utc)).seconds // 60
        raise HTTPException(403, f"Account locked. Try again in {remaining} minutes")
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        if db_user:
            db_user.failed_login_attempts += 1
            
            if db_user.failed_login_attempts >= 5:
                db_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.commit()
        raise HTTPException(401, "Invalid credentials")

    db_user.failed_login_attempts = 0
    db_user.locked_until = None
    db.commit()
    
    access = create_access_token(data={"sub": str(db_user.id)})
    refresh = create_refresh_token(data={"sub": str(db_user.id)})
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


@app.post("/refresh", response_model=Token)
@limiter.limit("7/minute")
def refresh(request: Request, req: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not verify_token_type(payload, "refresh"):
        raise HTTPException(401, "Invalid token type")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    new_access = create_access_token(data={"sub": user.id})
    return {"access_token": new_access, "refresh_token": req.refresh_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserOut)
@limiter.limit("100/minute")
def me(request: Request, current_user: User = Depends(get_current_user)):
    return current_user
# ========== Upload Profile Picture ==========
@app.post("/users/me/profile-picture", response_model=ProfilePictureResponse)
@limiter.limit("10/minute")
def upload_profile_picture(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ALLOWED_TYPES = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG and PNG files are allowed"
        )
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 2MB"
        )
    
    file_extension = file.filename.split(".")[-1].lower()
    unique_filename = f"{current_user.id}_{uuid4().hex}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    if current_user.profile_picture and os.path.exists(current_user.profile_picture):
        os.remove(current_user.profile_picture)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    current_user.profile_picture = file_path
    db.commit()
    
    return ProfilePictureResponse(
        message="Profile picture uploaded successfully",
        file_path=file_path
    )


@app.get("/users/me/profile-picture")
@limiter.limit("100/minute")
def get_profile_picture(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    if not current_user.profile_picture or not os.path.exists(current_user.profile_picture):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found"
        )
    return FileResponse(current_user.profile_picture)



# ========== FORGOT & RESET PASSWORD(Uncomment If You Already Have An Email For Using This) ==========

# @app.post("/forgot-password")
# @limiter.limit("5/day")
# async def forgot_password(email: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), request: Request):
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         return {"message":"If email exists, reset link will be sent"}

#     user.reset_token = secrets.token_urlsafe(32)
#     user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
#     db.commit()

#     background_tasks.add_task(send_reset_email, email, user.reset_token)

#     return {"message":"If email exists, reset link will be sent"}

# @app.post("/reset-password")
# @limiter.limit("5/day")
# async def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db), request: Request):
#     user = db.query(User).filter(User.reset_token == data.token, User.reset_token_expires > datetime.utcnow()).first()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid Or Expired Token"
#         )

#     user.hashed_password = get_password_hash(data.new_password)

#     user.reset_token = None
#     user.reset_token_expires = None
#     db.commit()

#     return {"message":"Password Reset Successfully"}


# ========== Email Verification(Uncomment If You Already Have An Email For Using This) ==========


# @app.post("/verify-email")
# @limiter.limit("5/minute")
# async def verify_email_endpoint(request: Request, data: VerifyEmailRequest, db: Session = Depends(get_db), ):

#     user = db.query(User).filter(
#         User.verification_code == data.code,
#         User.verification_code_expires > datetime.utcnow(),
#         User.is_verified == False
#     ).first()


#     if not user:
#         raise HTTPException(400, "Invalid or expired verification code")

#     user.is_verified = True
#     user.verification_code = None
#     user.verification_code_expires = None
#     db.commit()

#     return {"message":"Email Verified Successfully"}


# @app.post("/send-verification-email")
# @limiter.limit("20/day")
# async def send_verification_email_task(
#     request: Request,
#     background_tasks: BackgroundTasks,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db), 
# ):
#     if current_user.is_verified:
#         raise HTTPException(400, "Email Is Already Verified")
    
#     current_user.verification_code = secrets.token_urlsafe(32)
#     current_user.verification_expires = datetime.utcnow() + timedelta(hours=24)
#     db.commit()
    
#     background_tasks.add_task(
#         send_verification_email, 
#         current_user.email, 
#         current_user.verification_code
#     )
    
#     return {"message": "Verification Email Sent"}



# ========== POSTS ==========
@app.post("/posts", response_model=PostOut)
@limiter.limit("10/minute")
def create_post(request: Request, post: PostCreate, current_user: User = Depends(require_verified_user), db: Session = Depends(get_db)):
    db_post = Post(title=post.title, content=post.content, author_id=current_user.id, is_published=post.is_published)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/posts", response_model=dict)
@limiter.limit("100/minute")
def list_posts(request: Request, search: Optional[str] = Query(None, min_length=2, max_length=100, description="Search In Title And Content"), author_id: Optional[int] = Query(None, description="Filter Based On The Author ID"), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user_optional)):
    skip = (page - 1) * page_size

    query = db.query(Post).join(User).filter(User.is_active == True)
    if not current_user or not current_user.is_admin:
        query = query.filter(Post.is_published == True)
    if author_id:
        query = query.filter(Post.author_id == author_id)

    if search:
        query = query.filter((Post.title.ilike(f"%{search}%")) | (Post.content.ilike(f"%{search}%")))

    total = query.count()

    posts = query.order_by(Post.created_at.desc()).offset(skip).limit(page_size).all()
    

    result = []
    for p in posts:
        result.append({
            "id": p.id, "title": p.title, "content": p.content,
            "author_id": p.author_id, "created_at": p.created_at,
            "likes_count": db.query(Like).filter(Like.post_id == p.id).count(),
            "comments_count": db.query(Comment).filter(Comment.post_id == p.id).count()
        })
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "posts": result
    }

@app.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    
    likes_count = db.query(Like).filter(Like.post_id == post.id).count()
    comments_count = db.query(Comment).filter(Comment.post_id == post.id).count()
    
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author_id": post.author_id,
        "created_at": post.created_at,
        "is_published": post.is_published,
        "likes_count": likes_count,
        "comments_count": comments_count
    }

@app.put("/posts/{post_id}", response_model=PostOut)
@limiter.limit("10/minute")
def update_post(request: Request, post_id: int, post_update: PostUpdate, current_user: User = Depends(require_verified_user), db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(403, "Not authorized")
    if post_update.title is not None:
        post.title = post_update.title
    if post_update.content is not None:
        post.content = post_update.content
    if post_update.is_published is not None:
        post.is_published = post_update.is_published
    db.commit()
    db.refresh(post)
    return post

@app.delete("/posts/{post_id}", response_model=Message)
@limiter.limit("8/minute")
def delete_post(request: Request, post_id: int, current_user: User = Depends(require_verified_user), db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(403, "Not authorized")
    db.query(Like).filter(Like.post_id == post_id).delete()
    db.query(Comment).filter(Comment.post_id == post_id).delete()
    db.delete(post)
    db.commit()
    return Message(message="Post deleted")

# ========== Notifications ==========

@app.get("/notifications")
@limiter.limit("50/minute")
def get_notifications(
    request: Request,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    return notifications


@app.put("/notifications/{notification_id}/read")
@limiter.limit("30/minute")
def mark_notification_as_read(
    request: Request,
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(404, "Notification not found")
    
    notification.is_read = True
    db.commit()
    
    return {"message": "Notification marked as read"}

# ========== COMMENTS ==========
@app.post("/comments", response_model=CommentOut)
@limiter.limit("15/minute")
def add_comment(request: Request, comment: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    
    db_comment = Comment(content=comment.content, user_id=current_user.id, post_id=comment.post_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    if post.author_id != current_user.id:
        notification = Notification(
            user_id=post.author_id,
            actor_id=current_user.id,
            post_id=post.id,
            comment_id=db_comment.id,
            notification_type="comment",
            message=f"{current_user.username} Has Written A Comment Under Your Post: {comment.content[:50]}..."
        )
        db.add(notification)
        db.commit()

        asyncio.create_task(
            manager.send_personal_notification(
                post.author_id,
                f"{current_user.username} Has Written A Comment Under Your Post",
                "comment"
            )
        )
    return db_comment


@app.get("/posts/{post_id}/comments", response_model=List[CommentOut])
@limiter.limit("100/minute")
def get_comments(request: Request, post_id: int, db: Session = Depends(get_db)):
    return db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at).all()

@app.delete("/comments/{comment_id}", response_model=Message)
@limiter.limit("8/minute")
def delete_comment(request: Request, comment_id: int, current_user: User = Depends(require_verified_user), db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(404, "Comment not found")
    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(403, "Not authorized")
    db.delete(comment)
    db.commit()
    return Message(message="Comment deleted")

# ========== LIKES ==========
@app.post("/posts/{post_id}/like", response_model=Message)
@limiter.limit("20/minute")
def like_post(request: Request, post_id: int, current_user: User = Depends(require_verified_user), db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    
    existing = db.query(Like).filter(Like.user_id == current_user.id, Like.post_id == post_id).first()
    if existing:
        db.delete(existing)
        db.commit()

        db.query(Notification).filter(
            Notification.actor_id == current_user.id,
            Notification.post_id == post_id,
            Notification.notification_type == "like"
        ).delete()
        db.commit()
        return Message(message="Unliked")
    
    new_like = Like(user_id=current_user.id, post_id=post_id)
    db.add(new_like)
    db.commit()

    if post.author_id != current_user.id:
        notification = Notification(
            user_id=post.author_id,
            actor_id=current_user.id,
            post_id=post.id,
            notification_type="like",
            message=f"{current_user.username} Has Liked Your Post"
        )
        db.add(notification)
        db.commit()
    
        asyncio.create_task(
            manager.send_personal_notification(
                post.author_id,
                f"{current_user.username} پستت رو لایک کرد",
                "like"
            )
        )

    return Message(message="Liked")



@app.get("/posts/{post_id}/likes-count")
@limiter.limit("100/minute")
def like_count(request: Request, post_id: int, db: Session = Depends(get_db)):
    return {"post_id": post_id, "likes_count": db.query(Like).filter(Like.post_id == post_id).count()}

# ========== ADMIN ==========
@app.get("/admin/users", response_model=List[UserOut])
@limiter.limit("100/minute")
def admin_list_users(request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).all()

@app.put("/admin/users/{user_id}/deactivate", response_model=Message)
@limiter.limit("10/minute")
def admin_deactivate(request: Request, user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "Cannot deactivate yourself")
    user.is_active = False
    db.commit()
    return Message(message=f"User {user.username} deactivated")

# ========== ROOT ==========
@app.get("/")
@limiter.limit("100/minute")
def root(request: Request, ):
    return {"message": "Welcome", "docs": "/docs", "redoc": "/redoc"}


# ========== WebSocket(Notifications) ==========

@app.websocket("/ws/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    print(f"WebSocket connection attempt with token: {token[:50]}...")
    
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            print("No user_id in token")
            await websocket.close(code=1008, reason="Invalid token payload")
            return
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            print(f"User {user_id} not found or inactive")
            await websocket.close(code=1008, reason="User not found or inactive")
            return
            
    except Exception as e:
        print(f"Token validation error: {e}")
        await websocket.close(code=1008, reason=f"Token validation failed")
        return
    
    await manager.connect(int(user_id), websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(int(user_id))
    except Exception as e:
        print(f"Unexpected error: {e}")
        manager.disconnect(int(user_id))