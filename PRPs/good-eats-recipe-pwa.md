name: "GoodEats Recipe PWA - Full Stack Implementation"
description: |

## Purpose
Build a complete Progressive Web Application for recipe management with user accounts, social features, and advanced filtering. Implementation includes FastAPI backend with PostgreSQL, React frontend with PWA capabilities, rating system, and tag-based filtering.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create a production-ready recipe PWA where users can save personal recipes, share them publicly, discover new recipes through ratings and tags, and generate shopping lists. The application should be offline-capable, mobile-responsive, and scalable.

## Why
- **Business value**: Creates a comprehensive recipe management platform with social features
- **Integration**: Demonstrates modern full-stack development with PWA capabilities
- **Problems solved**: Recipe organization, discovery, meal planning, and shopping list generation
- **Future extensibility**: Architecture supports Chrome extension and mobile app integration

## What
A full-stack Progressive Web Application featuring:
- User authentication and personal cookbooks
- Public recipe sharing with upvote/downvote system
- Advanced tag-based filtering (protein, gluten-free, meal type, etc.)
- Shopping list generation from grouped recipes
- Offline-first PWA capabilities
- Mobile-responsive design using Tailwind and Flowbite

### Success Criteria
- [ ] Users can register, login, and manage personal recipes
- [ ] Public cookbook with voting system functional
- [ ] Tag filtering system with multiple categories working
- [ ] Shopping list generation from selected recipes
- [ ] PWA installable and works offline
- [ ] All API endpoints properly documented and tested
- [ ] Frontend responsive and follows design system
- [ ] Database properly indexed and performant

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://fastapi.tiangolo.com/tutorial/sql-databases/
  why: Official FastAPI database integration patterns
  
- url: https://github.com/fastapi/full-stack-fastapi-template
  why: Modern FastAPI + React + PostgreSQL project structure

- url: https://docs.sqlalchemy.org/en/20/tutorial/
  why: SQLAlchemy 2.0 async patterns and relationship management
  
- url: https://alembic.sqlalchemy.org/en/latest/tutorial.html
  why: Database migration patterns and best practices

- url: https://react.dev/
  why: Modern React patterns and hooks
  
- url: https://vite.dev/guide/
  why: Vite configuration and build optimization

- url: https://flowbite.com/docs/getting-started/react/
  why: Component library patterns and design system

- url: https://vite-pwa-org.netlify.app/guide/
  why: PWA implementation with Vite plugin

- url: https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps
  why: PWA best practices and offline strategies

- doc: https://stackoverflow.com/questions/20856/recommended-sql-database-design-for-tags-or-tagging
  why: Many-to-many tagging system design patterns

- doc: https://stackoverflow.com/questions/44987661/database-design-for-upvote-downvote-in-discussion-forum
  why: Voting system database design with PostgreSQL
```

### Current Codebase tree
```bash
.
├── CLAUDE.md                 # Project rules and guidelines
├── INITIAL.md               # Feature requirements
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md
│   └── EXAMPLE_multi_agent_prp.md
├── README.md                # Template documentation
├── examples/                # Template examples
└── use-cases/              # Various template use cases
```

### Desired Codebase tree with files to be added
```bash
good-eats/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── settings.py          # Environment configuration
│   │   │   └── database.py          # Database connection setup
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User SQLAlchemy model
│   │   │   ├── recipe.py           # Recipe SQLAlchemy model
│   │   │   ├── tag.py              # Tag and recipe_tags models
│   │   │   ├── vote.py             # Voting system model
│   │   │   └── shopping_list.py    # Shopping list models
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User Pydantic schemas
│   │   │   ├── recipe.py           # Recipe Pydantic schemas
│   │   │   ├── tag.py              # Tag Pydantic schemas
│   │   │   ├── vote.py             # Vote Pydantic schemas
│   │   │   └── shopping_list.py    # Shopping list schemas
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # Dependency injection
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── users.py            # User management endpoints
│   │   │   ├── recipes.py          # Recipe CRUD endpoints
│   │   │   ├── tags.py             # Tag management endpoints
│   │   │   ├── votes.py            # Voting system endpoints
│   │   │   └── shopping_lists.py   # Shopping list endpoints
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py         # JWT token handling
│   │   │   └── exceptions.py       # Custom exception handlers
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── email.py            # Email utilities (future)
│   ├── alembic/
│   │   ├── versions/               # Database migrations
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py             # Pytest configuration
│   │   ├── test_auth.py            # Authentication tests
│   │   ├── test_recipes.py         # Recipe endpoint tests
│   │   ├── test_tags.py            # Tag filtering tests
│   │   ├── test_votes.py           # Voting system tests
│   │   └── test_shopping_lists.py  # Shopping list tests
│   ├── requirements.txt            # Python dependencies
│   ├── alembic.ini                # Alembic configuration
│   └── Dockerfile                 # Backend container
├── frontend/
│   ├── public/
│   │   ├── manifest.json           # PWA manifest
│   │   ├── sw.js                   # Service worker
│   │   ├── icons/                  # PWA icons
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── Header.tsx      # Navigation component
│   │   │   │   ├── Layout.tsx      # App layout wrapper
│   │   │   │   ├── LoadingSpinner.tsx
│   │   │   │   └── ErrorBoundary.tsx
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx   # Login component
│   │   │   │   ├── RegisterForm.tsx # Register component
│   │   │   │   └── ProtectedRoute.tsx
│   │   │   ├── recipes/
│   │   │   │   ├── RecipeCard.tsx  # Recipe display card
│   │   │   │   ├── RecipeForm.tsx  # Recipe creation/edit
│   │   │   │   ├── RecipeDetail.tsx # Full recipe view
│   │   │   │   ├── RecipeList.tsx  # Recipe listing
│   │   │   │   └── VoteButtons.tsx # Upvote/downvote
│   │   │   ├── tags/
│   │   │   │   ├── TagFilter.tsx   # Tag filtering interface
│   │   │   │   ├── TagSelector.tsx # Tag selection component
│   │   │   │   └── TagCloud.tsx    # Popular tags display
│   │   │   └── shopping/
│   │   │       ├── ShoppingList.tsx # Shopping list view
│   │   │       └── IngredientGroup.tsx
│   │   ├── pages/
│   │   │   ├── Home.tsx            # Home page/recipe discovery
│   │   │   ├── Login.tsx           # Login page
│   │   │   ├── Register.tsx        # Registration page
│   │   │   ├── MyRecipes.tsx       # Personal cookbook
│   │   │   ├── PublicRecipes.tsx   # Public recipe browser
│   │   │   ├── RecipeDetail.tsx    # Recipe detail page
│   │   │   ├── CreateRecipe.tsx    # Recipe creation
│   │   │   ├── EditRecipe.tsx      # Recipe editing
│   │   │   └── ShoppingLists.tsx   # Shopping list management
│   │   ├── hooks/
│   │   │   ├── useAuth.tsx         # Authentication hook
│   │   │   ├── useRecipes.tsx      # Recipe data management
│   │   │   ├── useTags.tsx         # Tag management hook
│   │   │   ├── useVotes.tsx        # Voting functionality
│   │   │   └── useOffline.tsx      # PWA offline detection
│   │   ├── services/
│   │   │   ├── api.ts              # Axios configuration
│   │   │   ├── auth.ts             # Authentication API calls
│   │   │   ├── recipes.ts          # Recipe API calls
│   │   │   ├── tags.ts             # Tag API calls
│   │   │   ├── votes.ts            # Voting API calls
│   │   │   └── storage.ts          # LocalStorage utilities
│   │   ├── types/
│   │   │   ├── auth.ts             # Auth TypeScript types
│   │   │   ├── recipe.ts           # Recipe TypeScript types
│   │   │   ├── tag.ts              # Tag TypeScript types
│   │   │   └── api.ts              # API response types
│   │   ├── utils/
│   │   │   ├── constants.ts        # App constants
│   │   │   ├── validation.ts       # Form validation
│   │   │   └── formatting.ts       # Data formatting utilities
│   │   ├── App.tsx                 # Main app component
│   │   ├── main.tsx                # Vite entry point
│   │   └── index.css               # Global styles
│   ├── package.json                # Frontend dependencies
│   ├── vite.config.ts              # Vite configuration with PWA
│   ├── tailwind.config.js          # Tailwind configuration
│   ├── tsconfig.json               # TypeScript configuration
│   └── Dockerfile                  # Frontend container
├── docker-compose.yml              # Development orchestration
├── .env.example                    # Environment variables template
├── README.md                       # Project setup and documentation
└── .gitignore                      # Git ignore patterns
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: FastAPI requires async throughout - use async def for all endpoints
# CRITICAL: SQLAlchemy 2.0 async requires AsyncSession, not Session
# CRITICAL: Alembic migrations must be run in container for consistent schema
# CRITICAL: PostgreSQL array columns for tags require special querying syntax
# CRITICAL: PWA service worker must be properly registered for offline functionality
# CRITICAL: Vite requires explicit PWA plugin configuration for proper caching
# CRITICAL: JWT tokens should be stored in httpOnly cookies for security
# CRITICAL: Vote uniqueness enforced by composite primary key (user_id, recipe_id)
# CRITICAL: Recipe ingredients need proper JSON storage for shopping list grouping
# CRITICAL: Flowbite requires proper Tailwind configuration for components
# CRITICAL: Docker containers need proper health checks for production
```

## Implementation Blueprint

### Data models and structure

Create the core data models ensuring type safety and proper relationships.

```python
# SQLAlchemy Models Structure

# User Model
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    
    recipes: Mapped[List["Recipe"]] = relationship(back_populates="author")
    votes: Mapped[List["Vote"]] = relationship(back_populates="user")

# Recipe Model with JSON ingredients for shopping lists
class Recipe(Base):
    __tablename__ = "recipes"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(index=True)
    description: Mapped[Optional[str]]
    ingredients: Mapped[List[dict]] = mapped_column(JSON)  # For shopping list grouping
    instructions: Mapped[str]
    prep_time_minutes: Mapped[int]
    cook_time_minutes: Mapped[int]
    servings: Mapped[int]
    is_public: Mapped[bool] = mapped_column(default=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    upvotes: Mapped[int] = mapped_column(default=0)
    downvotes: Mapped[int] = mapped_column(default=0)
    vote_score: Mapped[int] = mapped_column(default=0)
    
    author: Mapped["User"] = relationship(back_populates="recipes")
    tags: Mapped[List["Tag"]] = relationship(secondary="recipe_tags", back_populates="recipes")
    votes: Mapped[List["Vote"]] = relationship(back_populates="recipe")

# Tag Model with PostgreSQL array optimization
class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    category: Mapped[str] = mapped_column(index=True)  # protein, dietary, meal_type, etc.
    
    recipes: Mapped[List["Recipe"]] = relationship(secondary="recipe_tags", back_populates="tags")

# Vote Model with composite primary key for uniqueness
class Vote(Base):
    __tablename__ = "votes"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), primary_key=True)
    vote_value: Mapped[int] = mapped_column(CheckConstraint("vote_value IN (-1, 1)"))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="votes")
    recipe: Mapped["Recipe"] = relationship(back_populates="votes")
```

### List of tasks to be completed in order

```yaml
Task 1: Backend Foundation Setup
CREATE backend/app/config/settings.py:
  - PATTERN: Use pydantic-settings for environment management
  - Load database URL, JWT secret, CORS origins
  - Include development and production configurations

CREATE backend/app/config/database.py:
  - PATTERN: Async SQLAlchemy 2.0 session management
  - Connection pooling configuration
  - Async session factory with proper cleanup

Task 2: Database Models and Migrations
CREATE backend/app/models/:
  - IMPLEMENT all SQLAlchemy models (user, recipe, tag, vote)
  - CONFIGURE proper relationships and indexes
  - ADD check constraints for vote values

CREATE alembic configuration:
  - SETUP alembic.ini with async database URL
  - CREATE initial migration with all tables
  - ADD indexes for performance (tags, recipe search, votes)

Task 3: Pydantic Schemas for API Validation
CREATE backend/app/schemas/:
  - IMPLEMENT request/response schemas for all models
  - ADD proper validation for email, passwords, recipe data
  - INCLUDE nested schemas for relationships (recipe with tags)

Task 4: Authentication System
CREATE backend/app/core/security.py:
  - IMPLEMENT JWT token creation and verification
  - ADD password hashing with bcrypt
  - CREATE dependency for current user authentication

CREATE backend/app/api/auth.py:
  - IMPLEMENT login, register, refresh token endpoints
  - ADD proper error handling for authentication failures
  - INCLUDE rate limiting for auth endpoints

Task 5: User Management
CREATE backend/app/api/users.py:
  - IMPLEMENT user profile CRUD operations
  - ADD current user retrieval endpoint
  - INCLUDE user deactivation functionality

Task 6: Recipe Management System
CREATE backend/app/api/recipes.py:
  - IMPLEMENT full CRUD for recipes
  - ADD filtering by tags, author, public/private
  - INCLUDE search functionality with text matching
  - ADD pagination for recipe lists

Task 7: Tag System Implementation
CREATE backend/app/api/tags.py:
  - IMPLEMENT tag CRUD operations
  - ADD tag categories (dietary, meal_type, protein, etc.)
  - INCLUDE popular tags endpoint
  - ADD recipe tag association management

Task 8: Voting System
CREATE backend/app/api/votes.py:
  - IMPLEMENT upvote/downvote functionality
  - ADD vote change detection (switch from up to down)
  - INCLUDE vote aggregation updates
  - ADD user vote status retrieval

Task 9: Shopping List Feature
CREATE backend/app/api/shopping_lists.py:
  - IMPLEMENT shopping list creation from multiple recipes
  - ADD ingredient grouping by similar items
  - INCLUDE quantity aggregation
  - ADD shopping list persistence

Task 10: FastAPI Application Setup
CREATE backend/app/main.py:
  - SETUP FastAPI application with CORS
  - INCLUDE all routers with proper prefixes
  - ADD exception handlers for common errors
  - CONFIGURE OpenAPI documentation

Task 11: Comprehensive Backend Testing
CREATE backend/tests/:
  - IMPLEMENT test fixtures for database and auth
  - ADD unit tests for all endpoints
  - INCLUDE integration tests for complex workflows
  - ENSURE 80%+ test coverage

Task 12: Frontend Foundation
CREATE frontend/src/services/api.ts:
  - SETUP Axios instance with interceptors
  - ADD automatic JWT token attachment
  - INCLUDE request/response logging
  - ADD error handling for common API errors

CREATE frontend/src/types/:
  - DEFINE TypeScript interfaces matching backend schemas
  - ADD API response type definitions
  - INCLUDE form validation types

Task 13: Authentication Components
CREATE frontend/src/components/auth/:
  - IMPLEMENT LoginForm with validation
  - CREATE RegisterForm with proper validation
  - ADD ProtectedRoute wrapper component
  - INCLUDE logout functionality

CREATE frontend/src/hooks/useAuth.tsx:
  - IMPLEMENT authentication state management
  - ADD login, register, logout functions
  - INCLUDE JWT token persistence
  - ADD user session management

Task 14: Recipe Management Components
CREATE frontend/src/components/recipes/:
  - IMPLEMENT RecipeCard for display
  - CREATE RecipeForm for creation/editing
  - ADD RecipeDetail with full information
  - INCLUDE RecipeList with pagination

CREATE frontend/src/hooks/useRecipes.tsx:
  - IMPLEMENT recipe data fetching
  - ADD CRUD operations
  - INCLUDE search and filtering
  - ADD optimistic updates

Task 15: Tag Filtering System
CREATE frontend/src/components/tags/:
  - IMPLEMENT TagFilter with multiple selections
  - CREATE TagSelector for recipe creation
  - ADD TagCloud for popular tag display
  - INCLUDE category-based tag grouping

CREATE frontend/src/hooks/useTags.tsx:
  - IMPLEMENT tag data management
  - ADD filtering state management
  - INCLUDE tag popularity calculation

Task 16: Voting System Frontend
CREATE frontend/src/components/recipes/VoteButtons.tsx:
  - IMPLEMENT upvote/downvote buttons
  - ADD visual feedback for user votes
  - INCLUDE vote count display
  - ADD animation for vote changes

CREATE frontend/src/hooks/useVotes.tsx:
  - IMPLEMENT voting functionality
  - ADD optimistic vote updates
  - INCLUDE vote status tracking

Task 17: Shopping List Feature
CREATE frontend/src/components/shopping/:
  - IMPLEMENT ShoppingList component
  - CREATE IngredientGroup for similar ingredients
  - ADD quantity editing
  - INCLUDE print functionality

Task 18: PWA Configuration
UPDATE frontend/vite.config.ts:
  - ADD vite-plugin-pwa configuration
  - CONFIGURE service worker for offline caching
  - INCLUDE manifest generation
  - ADD workbox strategies for different content types

CREATE frontend/src/hooks/useOffline.tsx:
  - IMPLEMENT offline detection
  - ADD offline notification
  - INCLUDE data synchronization on reconnection

Task 19: Page Components and Routing
CREATE frontend/src/pages/:
  - IMPLEMENT all page components
  - ADD React Router configuration
  - INCLUDE proper navigation
  - ADD breadcrumb navigation

Task 20: Styling and Responsive Design
CONFIGURE Tailwind with Flowbite:
  - SETUP component library integration
  - ADD responsive breakpoints
  - INCLUDE dark mode support
  - ADD custom design tokens

Task 21: Docker Configuration
CREATE docker-compose.yml:
  - SETUP PostgreSQL service
  - ADD backend service with proper dependencies
  - INCLUDE frontend service
  - ADD volume mounts for development

CREATE Dockerfiles:
  - OPTIMIZE backend container with multi-stage build
  - ADD frontend container with Nginx
  - INCLUDE health checks
  - ADD production configurations

Task 22: Documentation and Setup
CREATE README.md:
  - INCLUDE comprehensive setup instructions
  - ADD architecture overview
  - DOCUMENT API endpoints
  - INCLUDE contribution guidelines

CREATE .env.example:
  - LIST all required environment variables
  - ADD descriptions for each variable
  - INCLUDE example values
```

### Per task pseudocode for critical components

```python
# Task 6: Recipe Management with Tag Filtering
@router.get("/recipes/", response_model=List[RecipeResponse])
async def get_recipes(
    skip: int = 0,
    limit: int = 20,
    tags: List[str] = Query(None),
    search: str = None,
    is_public: bool = None,
    db: AsyncSession = Depends(get_db)
):
    # PATTERN: Build dynamic query with filters
    query = select(Recipe)
    
    if is_public is not None:
        query = query.where(Recipe.is_public == is_public)
    
    # CRITICAL: Tag filtering with array operations
    if tags:
        query = query.join(Recipe.tags).where(Tag.name.in_(tags))
    
    # PATTERN: Text search across multiple fields
    if search:
        query = query.where(
            or_(
                Recipe.title.ilike(f"%{search}%"),
                Recipe.description.ilike(f"%{search}%")
            )
        )
    
    # PATTERN: Pagination with offset/limit
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

# Task 8: Voting System with Aggregation
@router.post("/recipes/{recipe_id}/vote")
async def vote_recipe(
    recipe_id: int,
    vote_data: VoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # PATTERN: Upsert for vote changes
    existing_vote = await db.execute(
        select(Vote).where(
            Vote.user_id == current_user.id,
            Vote.recipe_id == recipe_id
        )
    )
    existing = existing_vote.scalar_one_or_none()
    
    if existing:
        # User changing vote
        old_value = existing.vote_value
        existing.vote_value = vote_data.vote_value
    else:
        # New vote
        new_vote = Vote(
            user_id=current_user.id,
            recipe_id=recipe_id,
            vote_value=vote_data.vote_value
        )
        db.add(new_vote)
        old_value = 0
    
    # CRITICAL: Update denormalized counts atomically
    recipe = await db.get(Recipe, recipe_id)
    if vote_data.vote_value == 1:  # Upvote
        recipe.upvotes += 1
        if old_value == -1:  # Changed from downvote
            recipe.downvotes -= 1
    else:  # Downvote
        recipe.downvotes += 1
        if old_value == 1:  # Changed from upvote
            recipe.upvotes -= 1
    
    recipe.vote_score = recipe.upvotes - recipe.downvotes
    
    await db.commit()
    return {"success": True, "vote_score": recipe.vote_score}

# Task 18: PWA Service Worker Strategy
// vite.config.ts PWA Configuration
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.goodEats\.com\/recipes/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'recipes-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 7 // 7 days
              }
            }
          },
          {
            urlPattern: /^https:\/\/api\.goodEats\.com\/tags/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'tags-cache'
            }
          }
        ]
      },
      manifest: {
        name: 'GoodEats Recipe Manager',
        short_name: 'GoodEats',
        description: 'Recipe management and discovery PWA',
        theme_color: '#10b981',
        icons: [
          {
            src: 'icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ]
});
```

### Integration Points
```yaml
DATABASE:
  - migrations: "All tables with proper indexes and constraints"
  - indexes: |
      CREATE INDEX idx_recipes_public ON recipes(is_public);
      CREATE INDEX idx_recipes_tags ON recipe_tags(tag_id);
      CREATE INDEX idx_votes_recipe ON votes(recipe_id);
      CREATE INDEX idx_recipes_author ON recipes(author_id);
      CREATE INDEX idx_recipes_vote_score ON recipes(vote_score DESC);

CONFIG:
  - add to: backend/app/config/settings.py
  - pattern: |
      DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/goodEats"
      JWT_SECRET_KEY = "your-secret-key"
      JWT_ALGORITHM = "HS256"
      JWT_EXPIRATION_HOURS = 24

ROUTES:
  - add to: backend/app/main.py
  - pattern: |
      app.include_router(auth_router, prefix="/auth", tags=["auth"])
      app.include_router(recipes_router, prefix="/recipes", tags=["recipes"])
      app.include_router(tags_router, prefix="/tags", tags=["tags"])
      app.include_router(votes_router, prefix="/votes", tags=["votes"])

FRONTEND_SERVICES:
  - add to: frontend/src/services/
  - pattern: |
      const api = axios.create({
        baseURL: import.meta.env.VITE_API_URL,
        withCredentials: true
      });
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Backend validation
cd backend && ruff check app/ --fix
cd backend && mypy app/
cd backend && pytest tests/ --cov=app --cov-report=term-missing

# Frontend validation  
cd frontend && npm run lint
cd frontend && npm run type-check
cd frontend && npm run test

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```python
# test_recipes.py
async def test_create_recipe():
    """Test recipe creation with tags"""
    recipe_data = {
        "title": "Test Recipe",
        "description": "A test recipe",
        "ingredients": [{"name": "flour", "amount": "2 cups"}],
        "instructions": "Mix ingredients",
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "servings": 4,
        "tag_ids": [1, 2]  # protein, dinner
    }
    response = await client.post("/recipes/", json=recipe_data)
    assert response.status_code == 201
    assert response.json()["title"] == "Test Recipe"
    assert len(response.json()["tags"]) == 2

async def test_vote_recipe():
    """Test upvote/downvote functionality"""
    # Create recipe first
    recipe = await create_test_recipe()
    
    # Test upvote
    response = await client.post(f"/recipes/{recipe.id}/vote", json={"vote_value": 1})
    assert response.status_code == 200
    assert response.json()["vote_score"] == 1
    
    # Test changing to downvote
    response = await client.post(f"/recipes/{recipe.id}/vote", json={"vote_value": -1})
    assert response.status_code == 200
    assert response.json()["vote_score"] == -1

async def test_tag_filtering():
    """Test recipe filtering by tags"""
    # Create recipes with different tags
    await create_recipe_with_tags(["protein", "dinner"])
    await create_recipe_with_tags(["vegetarian", "lunch"])
    
    response = await client.get("/recipes/?tags=protein")
    assert response.status_code == 200
    assert len(response.json()) == 1

# Frontend component tests
// RecipeCard.test.tsx
test('displays recipe information correctly', () => {
  const recipe = {
    id: 1,
    title: 'Test Recipe',
    description: 'A delicious test recipe',
    prep_time_minutes: 15,
    cook_time_minutes: 30,
    servings: 4,
    vote_score: 5,
    tags: [{ name: 'protein' }, { name: 'dinner' }]
  };
  
  render(<RecipeCard recipe={recipe} />);
  
  expect(screen.getByText('Test Recipe')).toBeInTheDocument();
  expect(screen.getByText('A delicious test recipe')).toBeInTheDocument();
  expect(screen.getByText('45 min total')).toBeInTheDocument();
  expect(screen.getByText('Serves 4')).toBeInTheDocument();
  expect(screen.getByText('5')).toBeInTheDocument(); // vote score
});

test('handles voting interactions', async () => {
  const mockVote = jest.fn();
  const recipe = { id: 1, title: 'Test', vote_score: 0 };
  
  render(<VoteButtons recipe={recipe} onVote={mockVote} />);
  
  await user.click(screen.getByLabelText('Upvote'));
  expect(mockVote).toHaveBeenCalledWith(1, 1);
});
```

```bash
# Run tests iteratively until passing:
cd backend && pytest tests/ -v --cov=app
cd frontend && npm run test -- --coverage

# If failing: Debug specific test, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start all services
docker-compose up -d

# Test API endpoints
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "first_name": "Test", "last_name": "User"}'

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'

# Test frontend PWA
# Expected: App loads at http://localhost:3000
# Can create account, login, create recipes
# Tags filter works properly
# Voting system functions
# PWA can be installed
# Works offline for cached content

# Test shopping list
# Expected: Can select multiple recipes and generate combined shopping list
# Ingredients are grouped by similarity
# Quantities are properly aggregated
```

## Final Validation Checklist
- [ ] All tests pass: `pytest backend/tests/ && npm run test --prefix frontend`
- [ ] No linting errors: `ruff check backend/app/` and `npm run lint --prefix frontend`  
- [ ] No type errors: `mypy backend/app/` and `npm run type-check --prefix frontend`
- [ ] Database migrations run cleanly: `alembic upgrade head`
- [ ] API documentation accessible at /docs endpoint
- [ ] User registration and authentication works
- [ ] Recipe CRUD operations functional
- [ ] Tag filtering system works with multiple selections
- [ ] Voting system properly aggregates and prevents duplicates
- [ ] Shopping list generation works from multiple recipes
- [ ] PWA installs and works offline
- [ ] Responsive design works on mobile and desktop
- [ ] Docker containers build and run correctly
- [ ] README has clear setup instructions
- [ ] Environment variables documented in .env.example

---

## Anti-Patterns to Avoid
- ❌ Don't use sync database operations in async FastAPI endpoints
- ❌ Don't store JWT tokens in localStorage - use httpOnly cookies
- ❌ Don't skip database indexes for frequently queried columns
- ❌ Don't allow duplicate votes - enforce with composite primary key
- ❌ Don't denormalize vote counts without proper atomic updates
- ❌ Don't hardcode API URLs - use environment variables
- ❌ Don't skip PWA manifest and service worker configuration
- ❌ Don't ignore error handling in async operations
- ❌ Don't create overly complex components - follow single responsibility
- ❌ Don't skip input validation on both frontend and backend
- ❌ Don't commit secrets or database credentials to repository

## Confidence Score: 9/10

High confidence due to:
- Comprehensive research on FastAPI + PostgreSQL patterns
- Clear database design for recipe management with voting and tags
- Modern PWA implementation with Vite and service workers
- Well-established patterns for authentication and API design
- Detailed task breakdown with specific implementation guidance
- Extensive validation gates ensuring working code

Minor uncertainty on shopping list ingredient grouping logic, but approach is well-documented and testable.