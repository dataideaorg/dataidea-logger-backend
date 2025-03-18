# DataIdea Logger - Backend API

A Django REST Framework-based API service for the DataIdea Logger, enabling secure logging of application data with proper authentication and authorization.

## Features

- **User Authentication**: JWT-based authentication system
- **API Key Management**: Generate and validate API keys for client applications
- **Logging API**: Endpoints for storing and retrieving log messages
- **User Management**: User registration and profile management
- **Admin Interface**: Django admin interface for managing data

## Technologies Used

- **Django 4.2+**: High-level Python web framework
- **Django REST Framework**: Toolkit for building Web APIs
- **JWT Authentication**: JSON Web Token authentication
- **SQLite/PostgreSQL**: Database storage (SQLite for development, PostgreSQL recommended for production)
- **CORS**: Cross-Origin Resource Sharing enabled for frontend integration

## API Endpoints

The API provides the following main endpoints:

- `/api/auth/register/` - User registration
- `/api/auth/login/` - User login (returns JWT tokens)
- `/api/auth/refresh/` - Refresh JWT token
- `/api/apikeys/` - List and create API keys
- `/api/apikeys/<id>/` - Retrieve, update, delete specific API key
- `/api/log/` - Create and list log messages
- `/api/log/<id>/` - Retrieve specific log message
- `/api/user/profile/` - User profile management

Full API documentation is available at `/api/docs/` when the server is running.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- virtualenv (recommended)

### Installation

1. Clone the repository
   ```
   git clone https://github.com/your-org/dataidea-logger.git
   cd dataidea-logger/backend
   ```

2. Create and activate a virtual environment
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables
   Create a `.env` file in the backend directory with the following:
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   CORS_ALLOWED_ORIGINS=http://localhost:5173
   ```

5. Run migrations
   ```
   python manage.py migrate
   ```

6. Create a superuser
   ```
   python manage.py createsuperuser
   ```

7. Start the development server
   ```
   python manage.py runserver
   ```

8. Access the admin interface at `http://localhost:8000/admin/`

## Database Configuration

By default, the application uses SQLite for development. For production, it's recommended to use PostgreSQL:

1. Install PostgreSQL and create a database
2. Update your `.env` file:
   ```
   DATABASE_URL=postgres://user:password@localhost:5432/dataidea_logger
   ```

## Creating Requirements File

If you add new dependencies, update the requirements file:

```
pip freeze > requirements.txt
```

## Testing

Run the test suite:

```
python manage.py test
```

## Deployment

For production deployment:

1. Set appropriate environment variables:
   ```
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com
   SECRET_KEY=your-secure-secret-key
   ```

2. Collect static files:
   ```
   python manage.py collectstatic
   ```

3. Configure a production-ready web server like Gunicorn with Nginx.

## Project Structure

```
backend/
├── main/                  # Project settings and configuration
├── logger/                # Main application code
│   ├── migrations/        # Database migrations
│   ├── models.py          # Data models
│   ├── serializers.py     # API serializers
│   ├── views.py           # API views
│   ├── urls.py            # URL routing
│   └── admin.py           # Admin interface configuration
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 