# MLB Season Simulator - Backend API

Django REST API backend for the MLB Season Simulator. Provides matchup analysis using **Pythagorean expectation** and **Elo ratings**.

---

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL database access
- pip (Python package manager)

---

## � Quick Start

### 1. Clone and Navigate

```bash
cd backend
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- Django 5.0.2
- djangorestframework 3.14.0
- django-cors-headers 4.3.1
- psycopg2-binary 2.9.9
- python-decouple 3.8
- numpy (for Monte Carlo simulations)

### 4. Configure Environment

Create a `.env` file in the backend directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=baseball_stats
DB_USER=myuser
DB_PASSWORD=mypassword
DB_HOST=ashlee.lu.im.ntu.edu.tw
DB_PORT=5433

# CORS Settings (Frontend URL)
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

> **Note**: `.env.example` is provided as a template. Copy it and modify with your credentials.

### 5. Run Database Migrations

```bash
# Check for any issues
python manage.py check

# Apply migrations
python manage.py migrate
```

This will create the `team_elo_history` table and other necessary database structures.


**Options:**
```bash
# Specify custom year range
python manage.py calculate_elo --start-year 2022 --end-year 2025

# Clear existing data and recalculate
python manage.py calculate_elo --clear-existing

# Custom K-factor (default: 20)
python manage.py calculate_elo --k-factor 25
```

### 6. Start Development Server

```bash
python manage.py runserver
```

Server will be available at: **http://localhost:8000**

---


### Check Database Connection

```bash
# Test database connection
python manage.py dbshell
```

If connection fails, verify your `.env` database credentials.

---

## 🔧 Common Commands

### Django Management

```bash
# Create superuser (for admin panel)
python manage.py createsuperuser

# Access admin panel at http://localhost:8000/admin/
```

### Database Operations

```bash
# Make migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# View current migration status
python manage.py showmigrations
```

### Elo Rating Management

```bash
# Recalculate Elo ratings
python manage.py calculate_elo --clear-existing

# Calculate for specific year range
python manage.py calculate_elo --start-year 2023 --end-year 2025

# View all options
python manage.py calculate_elo --help
```

### Development

```bash
# Run on different port
python manage.py runserver 8080

# Run tests
python manage.py test

# Check for issues
python manage.py check

# Collect static files (production)
python manage.py collectstatic
```

---

## 🐛 Troubleshooting

### 1. Database Connection Error

**Error:** `could not connect to server`

**Solution:**
```bash
# Verify database credentials in .env
# Test connection
python manage.py dbshell
```

### 2. Module Not Found

**Error:** `ModuleNotFoundError: No module named 'rest_framework'`

**Solution:**
```bash
# Ensure virtual environment is activated
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

### 3. Elo Ratings Not Found

**Error:** `Elo ratings not found for teams`

**Solution:**
```bash
# Calculate Elo ratings first
python manage.py calculate_elo
```

### 4. CORS Error (Frontend)

**Error:** `Access to fetch at 'http://localhost:8000' blocked by CORS policy`

**Solution:**
- Check `CORS_ALLOWED_ORIGINS` in `.env` includes your frontend URL
- Default: `http://localhost:5173` (Vite dev server)

### 5. NumPy Not Installed

**Error:** `No module named 'numpy'`

**Solution:**
```bash
pip install numpy
```

### 6. Migration Issues

**Error:** `No migrations to apply` or table not found

**Solution:**
```bash
# Reset migrations (CAREFUL: This will delete data)
python manage.py migrate api zero
python manage.py migrate
```

---


## 📄 License

This project is part of the MLB Sports Season Simulation application.

---

**Version**: 2.0.0  
**Last Updated**: 2025-11-30  
**Python**: 3.8+  
**Django**: 5.0.2
