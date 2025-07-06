# SecureTalkroom - Real-time Talkroom Application

A modern, scalable, and secure talkroom application built with Python, FastAPI, and WebSockets.

## Features

- 🔐 **JWT Authentication** - Secure user authentication with refresh tokens
- 💬 **Real-time Messaging** - WebSocket-based live talkroom functionality
- 🔒 **End-to-end Security** - Password hashing, input validation, and secure headers
- 📊 **PostgreSQL Database** - Robust data storage with SQLAlchemy ORM
- 🚀 **FastAPI Framework** - High-performance async API with automatic documentation
- 🐳 **Docker Support** - Containerized deployment with docker-compose
- 🧪 **Comprehensive Testing** - Unit tests, integration tests, and test coverage
- 🔍 **Code Quality** - Linting, formatting, and type checking
- 📈 **Monitoring Ready** - Health checks and logging
- 🌐 **CORS Support** - Cross-origin resource sharing configured

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **Real-time**: WebSocket connections
- **Caching**: Redis for session management
- **Testing**: pytest, pytest-asyncio, factory-boy
- **Code Quality**: black, flake8, mypy, isort
- **Deployment**: Docker, docker-compose, Nginx

## Project Structure

```
talkroom/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── users.py             # User management endpoints
│   │   └── talkroom.py          # Talkroom endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Application configuration
│   │   ├── database.py          # Database connection and session management
│   │   └── security.py          # Security utilities (JWT, password hashing)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User model
│   │   ├── talkroom.py          # Talkroom/Room model
│   │   └── message.py           # Message model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication schemas
│   │   ├── user.py              # User schemas
│   │   └── message.py           # Message and talkroom schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Authentication service
│   │   ├── user_service.py      # User service
│   │   └── talkroom_service.py  # Talkroom service
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── dependencies.py      # FastAPI dependencies
│   │   └── exceptions.py        # Custom exceptions
│   └── websocket/
│       ├── __init__.py
│       ├── connection_manager.py # WebSocket connection manager
│       └── talkroom_handler.py  # Talkroom WebSocket handler
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test configuration and fixtures
│   ├── test_auth.py             # Authentication tests
│   ├── test_users.py            # User management tests
│   ├── test_talkroom.py         # Talkroom functionality tests
│   └── integration/
│       ├── __init__.py
│       └── test_talkroom_flow.py # End-to-end tests
├── requirements/
│   ├── base.txt                 # Base dependencies
│   ├── dev.txt                  # Development dependencies
│   └── prod.txt                 # Production dependencies
├── docker/
│   ├── Dockerfile               # Application Docker image
│   └── nginx.conf               # Nginx configuration
├── scripts/
│   ├── run_tests.sh            # Test runner script
│   └── setup_dev.sh            # Development setup script
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD pipeline
├── alembic/                    # Database migrations
├── docker-compose.yml          # Multi-service Docker setup
├── pyproject.toml              # Project configuration
├── alembic.ini                 # Alembic configuration
└── README.md                   # This file

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (if running locally)
- Redis (if running locally)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/secure-talkroom.git
   cd secure-talkroom
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Using Docker (Recommended)**
   ```bash
   docker-compose up -d
   ```

4. **Manual Setup**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements/dev.txt

   # Setup database
   alembic upgrade head

   # Run the application
   uvicorn app.main:app --reload
   ```

### Development Setup

```bash
# Run the development setup script
./scripts/setup_dev.sh

# Or manually:
pre-commit install
python -m pytest --cov=app tests/
```

## API Documentation

Once the application is running, you can access:

- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

## Testing

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app tests/

# Run integration tests
pytest tests/integration/
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose build --no-cache
```

## Environment Variables

Key environment variables (see `.env.example`):

```bash
# Application
APP_NAME=SecureTalkroom
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=True

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/secure_talkroom
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/test_secure_talkroom

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://localhost:6379

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - User logout

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile
- `GET /api/v1/users/{user_id}` - Get user by ID

### Talkrooms
- `POST /api/v1/talkroom/` - Create new talkroom
- `GET /api/v1/talkroom/` - Get user's talkrooms
- `GET /api/v1/talkroom/{talkroom_id}/messages` - Get talkroom messages
- `POST /api/v1/talkroom/{talkroom_id}/messages` - Send message
- `PUT /api/v1/talkroom/{talkroom_id}/messages/{message_id}` - Edit message
- `DELETE /api/v1/talkroom/{talkroom_id}/messages/{message_id}` - Delete message

### WebSocket
- `WS /ws/talkroom/{token}` - Real-time talkroom connection

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for the powerful ORM
- [PostgreSQL](https://www.postgresql.org/) for the robust database
- [Redis](https://redis.io/) for caching and session management 