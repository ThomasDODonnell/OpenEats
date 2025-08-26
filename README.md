# 🍳 GoodEats Recipe PWA

A modern Progressive Web Application for recipe management with social features, built with FastAPI, React, and PostgreSQL.

## 🚀 Features

- **👤 User Authentication** - Secure JWT-based authentication system
- **📖 Recipe Management** - Create, edit, and share recipes with ingredients and instructions
- **🏷️ Smart Tagging** - Categorized tag system (dietary, cuisine, difficulty, etc.)
- **⭐ Community Voting** - Upvote/downvote system for recipe discovery
- **🔍 Advanced Search** - Filter by tags, cooking time, author, and text search
- **🛒 Shopping Lists** - Generate shopping lists from multiple recipes (planned)
- **📱 PWA Support** - Installable with offline capabilities (planned)
- **🎨 Responsive Design** - Mobile-first design with Tailwind CSS (planned)

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy 2.0** - Async ORM with proper relationship management
- **PostgreSQL** - Production database with advanced querying
- **Alembic** - Database migrations and schema management
- **Pydantic** - Data validation and settings management
- **JWT** - Secure authentication tokens
- **Docker** - Containerization for development and deployment

### Frontend (Planned)
- **React 18** - Modern React with hooks and context
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **Flowbite** - Component library for consistent UI
- **PWA** - Service workers for offline support

## 📋 Current Implementation Status

### ✅ Completed Backend Features

- [x] **Project Structure** - Complete backend architecture
- [x] **Database Models** - User, Recipe, Tag, Vote, ShoppingList models
- [x] **Authentication API** - Register, login, token management
- [x] **User Management** - Profile CRUD operations
- [x] **Recipe API** - Full CRUD with advanced filtering
- [x] **Tag System** - Categorized tags with popularity tracking
- [x] **Voting System** - Atomic upvote/downvote with aggregation
- [x] **Search & Filter** - Multi-criteria recipe filtering
- [x] **API Documentation** - Interactive OpenAPI/Swagger docs

### 🔄 In Progress

- [ ] Shopping list generation from recipes
- [ ] Frontend React application
- [ ] PWA configuration and service workers
- [ ] Docker containerization
- [ ] Comprehensive test suite

## 🏗️ Project Structure

```
GoodEats/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   │   ├── auth.py   # Authentication endpoints
│   │   │   ├── users.py  # User management
│   │   │   ├── recipes.py # Recipe CRUD with filtering
│   │   │   ├── tags.py   # Tag management
│   │   │   └── votes.py  # Voting system
│   │   ├── config/       # Configuration management
│   │   ├── core/         # Security and exceptions
│   │   ├── models/       # SQLAlchemy database models
│   │   ├── schemas/      # Pydantic validation schemas
│   │   └── utils/        # Utility functions
│   ├── alembic/          # Database migrations
│   ├── tests/            # Test suite
│   └── requirements.txt  # Python dependencies
├── frontend/             # React PWA (planned)
├── .env.example          # Environment configuration template
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or SQLite for development)
- Node.js 18+ (for frontend, when implemented)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd GoodEats
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp ../.env.example .env
   # Edit .env with your database URL and secret key
   ```

4. **Set up database**
   ```bash
   # For development with SQLite (in .env):
   # DATABASE_URL="sqlite+aiosqlite:///./goodEats.db"
   
   # For production with PostgreSQL:
   # DATABASE_URL="postgresql+asyncpg://username:password@localhost/goodEats_db"
   
   # Run migrations
   alembic upgrade head
   ```

5. **Start the API server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - API Root: http://localhost:8000/
   - Health Check: http://localhost:8000/health

## 📚 API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

- **Authentication**
  - `POST /auth/register` - Register new user
  - `POST /auth/login` - User login
  - `GET /auth/me` - Get current user info

- **Recipes**
  - `GET /recipes/` - List recipes with filtering
  - `POST /recipes/` - Create new recipe
  - `GET /recipes/{id}` - Get recipe details
  - `PUT /recipes/{id}` - Update recipe
  - `DELETE /recipes/{id}` - Delete recipe

- **Tags**
  - `GET /tags/` - List all tags
  - `GET /tags/popular` - Get popular tags by category
  - `POST /tags/` - Create new tag

- **Votes**
  - `POST /votes/recipes/{id}` - Vote on recipe
  - `GET /votes/recipes/{id}` - Get vote status
  - `DELETE /votes/recipes/{id}` - Remove vote

## 🧪 Testing

```bash
# Run tests (when implemented)
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## 🔧 Configuration

Key environment variables in `.env`:

```env
# Security (REQUIRED)
SECRET_KEY="your-super-secret-key"
DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"

# Optional
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]
JWT_EXPIRATION_HOURS=24
```

## 🏷️ Database Schema

### Core Models

- **Users** - Authentication and profile information
- **Recipes** - Recipe content with JSON ingredients for shopping lists
- **Tags** - Categorized tags for filtering (dietary, cuisine, etc.)
- **Votes** - Upvote/downvote system with composite primary key
- **Recipe_Tags** - Many-to-many relationship between recipes and tags

### Key Features

- **Async Operations** - All database operations use async/await
- **Proper Indexes** - Optimized for filtering and search queries
- **Vote Aggregation** - Denormalized vote counts for performance
- **JSON Ingredients** - Structured ingredient data for shopping lists

## 🌐 Deployment

### Development
```bash
uvicorn app.main:app --reload --port 8000
```

### Production (with Docker)
```bash
# Build and run (when Dockerfile is implemented)
docker build -t goodEats-api .
docker run -p 8000:8000 goodEats-api
```

## 🛣️ Roadmap

### Phase 1 - Core Backend ✅
- [x] Authentication system
- [x] Recipe CRUD operations
- [x] Tag system with categories
- [x] Voting functionality
- [x] Advanced filtering and search

### Phase 2 - Enhanced Features
- [ ] Shopping list generation
- [ ] User favorites and bookmarks
- [ ] Recipe import from URLs
- [ ] Image upload support
- [ ] Recipe rating system

### Phase 3 - Frontend PWA
- [ ] React application with TypeScript
- [ ] Progressive Web App features
- [ ] Offline recipe viewing
- [ ] Push notifications
- [ ] Mobile-responsive design

### Phase 4 - Advanced Features
- [ ] Social features (following users)
- [ ] Recipe collections and meal planning
- [ ] Nutritional information
- [ ] Recipe suggestions/recommendations
- [ ] Chrome extension for recipe import

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- SQLAlchemy for robust ORM capabilities
- Pydantic for data validation
- The open source community for inspiring this project

---

**Built with ❤️ for food lovers and home cooks everywhere** 🍳