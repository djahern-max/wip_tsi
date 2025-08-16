# TSI WIP Reporting Tool

A modern web application to replace confusing WIP spreadsheets with clean, calculated data and automated month-to-month comparisons.

## 🎯 Purpose

Transform complex Work-in-Progress (WIP) spreadsheets into:
- ✅ **Clean, organized data** with automatic calculations
- ✅ **Month-to-month comparisons** with variance tracking
- ✅ **Role-based access** (admin vs viewer)
- ✅ **Explanation system** for data transparency
- ✅ **Audit trails** for change tracking

## 🏗️ Architecture

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Frontend**: React + TypeScript (coming soon)
- **Authentication**: JWT with role-based permissions
- **Database**: PostgreSQL with Alembic migrations

## 📊 Features

### Core WIP Functionality
- **Contract tracking** (original amounts, change orders, totals)
- **Cost management** (costs to date, estimated completion costs)
- **US GAAP calculations** (% completion, revenue recognition)
- **Job margin analysis** (dollar amounts and percentages)
- **WIP adjustments** (costs/billings in excess)

### Business Logic
- **Automatic calculations** when base data changes
- **Month-to-month variance** tracking
- **Data validation** and business rule enforcement
- **Smart comparisons** with prior periods

### User Management
- **Role-based access**: Admin (edit) vs Viewer (read-only)
- **Secure authentication** with JWT tokens
- **User activity tracking**

### Explanation System
- **Field-level comments** for data transparency
- **Visual indicators** for explained data
- **Change tracking** with user attribution

## 🚀 Getting Started

### Prerequisites
- Python 3.11+ 
- PostgreSQL 12+
- Node.js 16+ (for frontend, when ready)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/djahern-max/wip_tsi.git
   cd wip_tsi/backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb wip_reporting_db
   
   # Run migrations
   alembic upgrade head
   ```

6. **Initialize data**
   ```bash
   # Create users, projects, and sample WIP data
   python3 scripts/setup_all_data.py
   ```

7. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

8. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 🔐 Default Users

All users have password: `123456`

**Admin User:**
- `dahern@gototsi.com` (can create/edit data)

**Viewer Users:**
- `kulike@muehlhan.com`
- `mueler-arends@muehlhan.com` 
- `brockman@muehlhan.com`
- `paulb@gototsi.com`
- `evans@muehlhan.com`
- `walz@muehlhan.com`
- `zaczeniuk@muehlhan.com`
- `nedal@muehlhan.com`
- `hell@muehlhan.com`

## 📖 API Usage

### Authentication
```bash
# Login to get token
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "dahern@gototsi.com", "password": "123456"}'
```

### WIP Data
```bash
# Get latest WIP snapshots
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/wip/latest

# Get dashboard summary
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/wip/summary/dashboard
```

## 🗂️ Project Structure

```
backend/
├── app/
│   ├── api/endpoints/     # API route handlers
│   ├── core/             # Configuration & security
│   ├── db/               # Database setup
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── main.py           # FastAPI application
├── alembic/              # Database migrations
├── scripts/              # Setup & utility scripts
├── tests/                # Test files
└── requirements.txt      # Dependencies
```

## 🧮 WIP Calculations

The system automatically calculates dependent fields:

**Input Fields** (user enters):
- Original contract amount
- Change order amount  
- Cost to date
- Estimated cost to complete
- Revenue billed to date

**Calculated Fields** (automatic):
- Total contract amount = original + change orders
- Estimated final cost = cost to date + estimated to complete
- US GAAP % completion = cost to date ÷ estimated final cost
- Revenue earned = contract amount × % completion
- Job margin = contract amount - estimated final cost
- WIP adjustments based on revenue vs costs vs billings

## 🔧 Development

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

### Testing
```bash
# Run tests
python3 -m pytest tests/ -v
```

## 📈 Current Data

The system includes **28 active projects** with **$43.1M total contract value**:
- Projects from job #2215 to #2509
- July 2025 WIP snapshots with contract data
- Automatic calculations for all derived fields

## 🛣️ Roadmap

- [ ] React frontend with dashboard views
- [ ] Excel import/export functionality  
- [ ] Advanced reporting and analytics
- [ ] Email notifications for significant changes
- [ ] Mobile-responsive design
- [ ] Bulk data entry capabilities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is proprietary software for TSI internal use.

---

**Built to eliminate spreadsheet confusion and bring clarity to WIP reporting! 📊✨**