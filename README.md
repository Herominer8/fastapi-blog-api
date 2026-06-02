# 📝 FastAPI Blog API

A production-ready RESTful API for a blog platform with user authentication, posts, comments, likes, real-time notifications, and advanced security features. Built with FastAPI, SQLAlchemy, JWT, and WebSockets.

---

## ✨ Features

### 🔐 Authentication & Security
- JWT-based authentication with Access & Refresh Tokens
- Secure password hashing with bcrypt (12 rounds)
- Account lockout after 5 failed login attempts (15 minutes lock)
- Rate limiting per endpoint (IP-based)
- Email verification flow (disabled by default)
- Password reset flow with secure tokens (disabled by default)
- CORS configured for frontend integration

### 👥 User Management
- User registration and login
- Profile management with profile picture upload
- User deactivation (admin only)
- Admin panel for user management

### 📝 Blog Posts
- Full CRUD operations (Create, Read, Update, Delete)
- Pagination with metadata (page, page_size, total, total_pages)
- Search in title and content
- Filter by author ID and publish status
- Sorting by creation date, title, or like count
- Author-only edit/delete permissions

### 💬 Comments & ❤️ Likes
- Add and delete comments (author or admin only)
- Like/unlike posts with toggle functionality
- Automatic like and comment counts for each post
- Real-time notifications via WebSocket when someone comments or likes your post

### 👑 Admin Panel
- View all registered users
- Deactivate user accounts (admin only)
- Cannot deactivate own account

### ⚡ Real-Time Features
- WebSocket connection with JWT authentication
- Instant notifications for likes and comments
- Connection manager for active users

### 🧪 Testing
- 25+ unit and integration tests with pytest
- Test coverage for authentication, posts, comments, likes, and admin endpoints
- Async test support with pytest-asyncio
- Parallel test execution with pytest-xdist
- Timeout protection for slow tests

### 🗄️ Database
- SQLAlchemy ORM with Alembic migrations
- SQLite by default (easily swappable with PostgreSQL)
- Proper foreign key relationships and constraints
- Unique constraint on user-post likes

### 📁 File Upload
- Profile picture upload (JPEG, PNG, max 2MB)
- Unique filename generation with UUID
- Automatic deletion of old profile pictures

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite / PostgreSQL |
| Auth | JWT with python-jose |
| Password Hashing | bcrypt via passlib |
| Validation | Pydantic V2 |
| Rate Limiting | SlowAPI |
| Database Migration | Alembic |
| Testing | Pytest, pytest-asyncio, pytest-xdist, pytest-timeout |
| WebSocket | FastAPI WebSocket |
| File Upload | Python UploadFile |
| Server | Uvicorn |

---

## 📁 Project Structure
blog/
├── app/
│ ├── init.py
│ ├── main.py # Application entry point
│ ├── models.py # SQLAlchemy ORM models
│ ├── schemas.py # Pydantic schemas
│ ├── websocket_manager.py # WebSocket connection manager
│ │
│ └── core/
│ ├── init.py
│ ├── config.py # Environment configuration
│ ├── database.py # Database connection
│ ├── security.py # Password hashing, JWT, CORS
│ └── dependencies.py # Authentication dependencies
│
├── tests/ # Test files
│ ├── test_auth.py
│ ├── test_posts.py
│ ├── test_comments.py
│ ├── test_likes.py
│ ├── test_admin.py
│ └── test_websocket_notifications.py
│
├── uploads/ # Uploaded profile pictures
├── .env # Environment variables
├── .gitignore
├── requirements.txt
├── alembic.ini
└── README.md


---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/Herominer8/your-repo-name
cd your-repo-name

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF

# Run database migrations
alembic upgrade head

# Run the application
uvicorn app.main:app --reload

📖 API Documentation
After running the server, visit:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

🔌 API Endpoints
Authentication
Method	Endpoint	Description	Auth Required
POST	/register	Register new user	❌
POST	/login	Login and get JWT tokens	❌
POST	/refresh	Refresh access token	❌
GET	/users/me	Get current user profile	✅


Profile Picture
Method	Endpoint	Description	Auth Required
POST	/users/me/profile-picture	Upload profile picture	✅
GET	/users/me/profile-picture	Get profile picture	✅


Posts
Method	Endpoint	Description	Auth Required
GET	/posts	List all posts (paginated, searchable, filterable)	❌
GET	/posts/{id}	Get single post	❌
POST	/posts	Create new post	✅
PUT	/posts/{id}	Update post	✅ (author or admin)
DELETE	/posts/{id}	Delete post	✅ (author or admin)


Comments
Method	Endpoint	Description	Auth Required
POST	/comments	Add comment to post	✅
GET	/posts/{id}/comments	Get all comments for a post	❌
DELETE	/comments/{id}	Delete comment	✅ (author or admin)


Likes
Method	Endpoint	Description	Auth Required
POST	/posts/{id}/like	Toggle like/unlike	✅
GET	/posts/{id}/likes-count	Get like count for post	❌


Notifications
Method	Endpoint	Description	Auth Required
GET	/notifications	Get user notifications	✅
PUT	/notifications/{id}/read	Mark notification as read	✅
WebSocket	/ws/notifications?token={token}	Real-time notifications	✅

Admin
Method	Endpoint	Description	Auth Required
GET	/admin/users	List all users	✅ (admin only)
PUT	/admin/users/{id}/deactivate	Deactivate user account	✅ (admin only)

🧪 Testing with cURL
Register a user

curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"secret123"}'

Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"secret123"}'

Create a post (with token)
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"title":"My First Post","content":"Hello World!","is_published":true}'

Like a post
curl -X POST http://localhost:8000/posts/1/like \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

Get paginated posts with search and filter
curl -X GET "http://localhost:8000/posts?page=1&page_size=10&search=hello&author_id=1"



🔧 Environment Variables
Variable	Description	Default	Required
SECRET_KEY	JWT signing key	None	✅ Yes
ALGORITHM	JWT signing algorithm	HS256	❌ No
ACCESS_TOKEN_EXPIRE_MINUTES	Access token expiration	30	❌ No
REFRESH_TOKEN_EXPIRE_DAYS	Refresh token expiration	7	❌ No



📦 Dependencies
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.10.4
pydantic-settings==2.7.0
python-dotenv==1.0.1
email-validator==2.2.0
bcrypt==4.3.0
alembic==1.14.1
slowapi==0.1.9
fastapi-mail==1.6.4
pytest==9.0.3
pytest-asyncio==1.3.0
pytest-xdist==3.8.0
pytest-timeout==2.4.0
websockets==15.0.1


🗄️ Database
The project uses SQLite by default (file: blogdb.db). To switch to PostgreSQL:

# In app/core/database.py
DATABASE_URL = "postgresql://user:pass@localhost/dbname"

Then install:
pip install psycopg2-binary

Then run migrations:
alembic upgrade head


🧪 Running Tests

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term

# Run tests in parallel (4 workers)
pytest tests/ -n 4

# Run with timeout protection (10 seconds per test)
pytest tests/ --timeout=10



🔒 Security Features
Passwords hashed with bcrypt (12 rounds)

JWT tokens with configurable expiration

Refresh token rotation

Account lockout after 5 failed login attempts (15 minutes)

Rate limiting on all endpoints

Admin-only endpoints

Row-level authorization (users can only edit/delete their own content)

CORS configured for frontend integration

Environment variables for sensitive data

Email verification and password reset flows (with secure tokens)

Profile picture validation (file type and size)

WebSocket authentication via JWT token




📝 Future Improvements
Redis caching for frequently accessed data

Token blacklisting with Redis (logout functionality)

Docker containerization

CI/CD pipeline with GitHub Actions

Deployment on Railway/Render

Email verification and password reset (currently disabled)

More comprehensive test coverage

Performance benchmarking


🤝 Contributing
1.Fork the repository

2.Create a feature branch (git checkout -b feature/amazing-feature)

3.Commit your changes (git commit -m 'Add some amazing feature')

4.Push to the branch (git push origin feature/amazing-feature)

5.Open a Pull Request


📄 License
Distributed under the MIT License. See LICENSE file for more information.


👨‍💻 Author
Herominer8

GitHub: @Herominer8



⭐ Show Your Support
If this project helped you, please give it a star ⭐ on GitHub!