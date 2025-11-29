# MLB Season Simulator - Backend

Django REST API backend for the MLB Season Simulator application. This backend serves as a proxy to the MLB Stats API and provides API endpoints for team and roster data.

## 🛠️ Technology Stack

- **Framework**: Django 5.0.2
- **API**: Django REST Framework 3.14.0
- **Database**: PostgreSQL (via psycopg2-binary)
- **CORS**: django-cors-headers
- **HTTP Client**: requests

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL database access
- pip (Python package manager)

## 🚀 Setup Instructions

### 1. Create Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the backend directory:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=baseball_stats
DB_USER=myuser
DB_PASSWORD=mypassword
DB_HOST=ashlee.lu.im.ntu.edu.tw
DB_PORT=5433

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 4. Run Database Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The server will start at `http://localhost:8000`

## 📡 API Endpoints

### Get Teams List

```http
GET /api/teams/
```

**Response:**
```json
{
  "teams": [
    {
      "id": 109,
      "name": "Los Angeles Dodgers"
    },
    {
      "id": 147,
      "name": "New York Yankees"
    }
  ]
}
```

### Get Team Roster

```http
GET /api/teams/{team_id}/roster/
```

**Parameters:**
- `team_id` (integer): MLB team ID

**Response:**
```json
{
  "roster": [
    {
      "id": 660271,
      "name": "Shohei Ohtani",
      "position": "DH",
      "rating": 98
    },
    {
      "id": 592450,
      "name": "Mookie Betts",
      "position": "RF",
      "rating": 95
    }
  ]
}
```

## 🗄️ Database Configuration

The application is configured to connect to a PostgreSQL database with the following configuration:

```python
DB_CONFIG = {
    "dbname": "baseball_stats",
    "user": "myuser",
    "password": "mypassword",
    "host": "ashlee.lu.im.ntu.edu.tw",
    "port": "5433"
}
```

Update these values in your `.env` file as needed.

## 🔧 Project Structure

```
backend/
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── sports_simulator/          # Django project directory
│   ├── __init__.py
│   ├── settings.py           # Django settings with DB config
│   ├── urls.py               # Main URL routing
│   ├── wsgi.py               # WSGI configuration
│   └── asgi.py               # ASGI configuration
└── api/                       # API application
    ├── __init__.py
    ├── apps.py
    ├── models.py             # Database models
    ├── views.py              # API views
    ├── urls.py               # API URL routing
    ├── services.py           # MLB Stats API integration
    ├── admin.py              # Django admin configuration
    └── tests.py              # Unit tests
```

## 🧪 Testing

Run tests with:

```bash
python manage.py test
```

## 📝 Features

- **MLB Stats API Proxy**: Fetches team and roster data from MLB Stats API
- **Fallback Data**: Provides mock data if API is unavailable
- **Deterministic Rating System**: Generates consistent player ratings using FNV-1a hash
- **CORS Support**: Configured for frontend development server
- **PostgreSQL Integration**: Ready for database operations
- **REST API**: Clean JSON API endpoints

## 🔐 Admin Panel

Access the Django admin panel at `http://localhost:8000/admin/` after creating a superuser.

## 🌐 Integration with Frontend

The frontend should be configured to call these backend endpoints. The CORS settings allow requests from `http://localhost:5173` (Vite default port).

**Note**: The current implementation keeps the frontend unchanged - it continues to call MLB Stats API directly. To use this backend as a proxy, update the frontend API calls to point to `http://localhost:8000/api/` instead.

## 📚 Additional Commands

```bash
# Make migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Collect static files (for production)
python manage.py collectstatic

# Run development server on specific port
python manage.py runserver 8080
```

## 🐛 Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running and accessible
- Check database credentials in `.env`
- Ensure host and port are correct

### CORS Errors
- Verify frontend URL in `CORS_ALLOWED_ORIGINS`
- Check that `corsheaders` middleware is enabled

### Module Not Found Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

## 📄 License

This project is part of the Sports Season Simulation application.
