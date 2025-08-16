# TSI WIP Reporting Tool - Backend API

FastAPI backend for the TSI WIP Reporting Tool - replacing confusing spreadsheets with clean, calculated data.

## 🎯 Purpose

Backend API that provides:
- ✅ **Automatic WIP calculations** (contract totals, margins, % completion)
- ✅ **Month-to-month comparisons** with variance tracking
- ✅ **Role-based authentication** (admin vs viewer)
- ✅ **Explanation system** for data transparency
- ✅ **RESTful API** for frontend integration

## 🏗️ Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Robust database for financial data
- **SQLAlchemy** - ORM with relationship management
- **Alembic** - Database migrations
- **JWT Authentication** - Secure token-based auth
- **Pydantic** - Data validation and serialization

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+

### Installation

1. **Clone and setup**
   ```bash
   git clone https://github.com/djahern-max/wip_tsi_backend.git
   cd wip_tsi_backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Setup database**
   ```bash
   createdb wip_reporting_db
   alembic upgrade head
   python3 scripts/setup_all_data.py
   ```

4. **Start server**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access API docs**
   - http://localhost:8000/docs (Swagger UI)
   - http://localhost:8000/redoc (ReDoc)

## 🔐 Authentication

### Default Users
Password for all users: `123456`

**Admin** (can create/edit):
- `dahern@gototsi.com`

**Viewers** (read-only):
- `kulike@muehlhan.com`, `brockman@muehlhan.com`, etc.

### Usage
```bash
# Login
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "dahern@gototsi.com", "password": "123456"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/wip/latest
```

## 📊 API Endpoints

### Authentication
- `POST /auth/login` - Login and get JWT token
- `POST /auth/verify-token` - Verify token validity

### Projects
- `GET /projects/` - List all projects
- `GET /projects/{id}` - Get specific project
- `POST /projects/` - Create project (admin only)
- `PUT /projects/{id}` - Update project (admin only)

### WIP Data
- `GET /wip/` - List WIP snapshots (with filters)
- `GET /wip/latest` - Latest snapshot per project
- `GET /wip/{id}` - Get specific WIP snapshot
- `POST /wip/` - Create WIP snapshot (admin only)
- `PUT /wip/{id}` - Update WIP snapshot (admin only)
- `GET /wip/compare/{project_id}` - Month-to-month comparison
- `GET /wip/summary/dashboard` - Dashboard statistics

### Explanations
- `GET /explanations/wip/{wip_id}` - Get explanations
- `POST /explanations/wip/{wip_id}` - Add explanation (admin only)
- `GET /explanations/fields/available` - Available fields

### Users
- `GET /users/me` - Current user info
- `GET /users/` - List users (admin only)

## 🧮 Automatic Calculations

The system calculates dependent fields when you input base data:

**Input** (what users enter):
- Original contract amount: `$1,000,000`
- Change orders: `$50,000`
- Cost to date: `$600,000`
- Estimated cost to complete: `$300,000`
- Billed to date: `$700,000`

**Output** (automatically calculated):
- Total contract: `$1,050,000` (original + change orders)
- Estimated final cost: `$900,000` (cost to date + est. to complete)
- % Complete: `66.67%` (cost to date ÷ final cost)
- Revenue earned: `$700,000` (contract × % complete)
- Job margin: `$150,000` (contract - final cost)
- Margin %: `14.29%` (margin ÷ contract)

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/endpoints/     # API route handlers
│   │   ├── auth.py       # Authentication
│   │   ├── projects.py   # Project management
│   │   ├── wip.py        # WIP data operations
│   │   ├── explanations.py # Comment system
│   │   └── users.py      # User management
│   ├── core/             # Configuration & security
│   ├── db/               # Database setup
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── main.py           # FastAPI application
├── alembic/              # Database migrations
├── scripts/              # Setup & utility scripts
└── requirements.txt      # Dependencies
```

## 💾 Current Data

**28 Projects** totaling **$43.1M contract value**:
- Job numbers: 2215 through 2509
- July 2025 WIP snapshots with contract data
- Automatic calculations for all derived fields

## 🔧 Development

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations  
alembic upgrade head
```

### Testing
```bash
python3 -m pytest tests/ -v
```

### Code Quality
```bash
black app/
isort app/
flake8 app/
```

## 🌐 Frontend Integration

This backend provides a complete REST API for frontend integration:

- **CORS enabled** for local development
- **JWT authentication** with role-based permissions
- **Comprehensive error handling** with proper HTTP status codes
- **OpenAPI documentation** for easy integration
- **Pydantic schemas** for type safety

## 📈 Key Features

### WIP Calculation Engine
- **Automatic field calculations** when base data changes
- **Month-to-month variance** tracking
- **Business rule validation** 
- **Prior period comparisons**

### Security
- **JWT token authentication**
- **Role-based access control** (admin/viewer)
- **Password hashing** with bcrypt
- **Input validation** and sanitization

### Data Management
- **Comprehensive audit trails**
- **Field-level explanations**
- **Bulk operations** support
- **Database constraints** for data integrity

---

**Ready to power your WIP reporting frontend! 🚀**