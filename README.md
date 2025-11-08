# Mood Tracker Backend API

Flask REST API backend for the Mood Tracker application. This backend provides secure mood tracking, analytics, and insights via a RESTful API that serves the Flutter frontend.

## Architecture

Clean layered architecture following SOLID principles:

```
┌─────────────────────────────────────────────────────────┐
│                     Routes Layer                        │
│  (HTTP Concerns - Request/Response handling)            │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   Service Layer                         │
│  (Business Logic - Mood tracking, Analytics, Insights)  │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 Repository Layer                        │
│  (Data Access - Database operations)                    │
└─────────────────────────────────────────────────────────┐
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│         PostgreSQL Database (Railway)                   │
└─────────────────────────────────────────────────────────┘
```

### SOLID Principles Applied
- **S**ingle Responsibility: Each class has one reason to change
- **O**pen/Closed: Open for extension, closed for modification
- **L**iskov Substitution: Interfaces ensure substitutability
- **I**nterface Segregation: Clients depend only on needed methods
- **D**ependency Inversion: Depend on abstractions, not concretions

## Features

### Authentication
- OAuth 2.0 with Google & GitHub
- User-specific data isolation
- Session management with Flask-Login
- No password storage

### Core API
- **Mood Tracking**: 7-level mood system with notes
- **Analytics**: Streaks, patterns, trends
- **Insights**: AI-generated mood insights
- **Tags**: Categorize and filter moods
- **Export**: PDF reports with charts
- **Goals**: Mood tracking goals

### Advanced Features
- Timezone handling (UTC-3 Chile)
- Real-time health monitoring
- Weekly/daily patterns analysis
- Migration endpoints for data management

## Tech Stack

- **Python 3.11+** with Flask 2.3.3
- **PostgreSQL** with psycopg3
- **OAuth 2.0** for authentication
- **ReportLab** for PDF generation
- **Dependency Injection** with custom container

## API Endpoints

### Authentication
```
GET  /login                  - Login page
GET  /auth/<provider>        - OAuth redirect (google/github)
GET  /callback/<provider>    - OAuth callback
GET  /logout                 - Logout user
```

### Mood Tracking
```
POST /save_mood              - Save/update mood entry
GET  /                       - Dashboard (requires auth)
```

### Analytics
```
GET  /mood_data              - Monthly trend data
GET  /weekly_patterns        - Weekly pattern analysis
GET  /daily_patterns         - Daily pattern analysis
GET  /analytics-health       - Analytics system health
```

### Export & Reports
```
GET  /export_pdf             - Generate PDF report
```

### Health & Monitoring
```
GET  /health                 - Database health check
GET  /status                 - Basic app status
GET  /debug-oauth            - OAuth configuration (dev)
```

## Installation

### Local Development

1. **Clone repository**:
```bash
git clone https://github.com/alsophocus/mood-tracker-app-backend.git
cd mood-tracker-app-backend
```

2. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Run the API**:
```bash
python app.py
```

API will be available at `http://localhost:5000`

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# OAuth - Google
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# OAuth - GitHub
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Flask
SECRET_KEY=your_random_secret_key
```

## Railway Deployment

### Setup

1. Create PostgreSQL service in Railway
2. Connect this GitHub repository
3. Set environment variables (Railway auto-provides DATABASE_URL)
4. Deploy automatically on push to main

### Railway Configuration

The `railway.json` file configures:
```json
{
  "deploy": {
    "startCommand": "python app.py"
  }
}
```

### Environment Variables (Railway)
- `DATABASE_URL`: Auto-provided by PostgreSQL service
- `GOOGLE_CLIENT_ID`: Add in Variables tab
- `GOOGLE_CLIENT_SECRET`: Add in Variables tab
- `GITHUB_CLIENT_ID`: Add in Variables tab
- `GITHUB_CLIENT_SECRET`: Add in Variables tab
- `SECRET_KEY`: Add in Variables tab

### OAuth Redirect URIs

Configure in Google/GitHub OAuth apps:
```
https://your-service.railway.app/callback/google
https://your-service.railway.app/callback/github
```

## Frontend Integration

This backend serves a Flutter frontend:
- **Frontend Repository**: https://github.com/alsophocus/mood-tracker-app-frontend
- **Communication**: REST API via HTTP/HTTPS
- **Authentication**: OAuth tokens managed by backend
- **CORS**: Enabled for web deployment

## Database Schema

### Users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    provider TEXT NOT NULL
);
```

### Moods
```sql
CREATE TABLE moods (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    date DATE NOT NULL,
    mood TEXT NOT NULL,
    notes TEXT,
    UNIQUE(user_id, date)
);
```

## Project Structure

```
mood-tracker-app-backend/
├── routes.py                 # Main API routes
├── admin_routes.py           # Admin endpoints
├── comprehensive_routes.py   # Additional routes
├── insights_routes.py        # Insights API
├── services.py               # Business logic
├── analytics.py              # Analytics engine
├── models.py                 # Domain models
├── interfaces.py             # Repository interfaces
├── database.py               # Repository implementations
├── auth.py                   # OAuth authentication
├── container.py              # Dependency injection
├── app.py                    # Application entry point
├── config.py                 # Configuration
├── requirements.txt          # Python dependencies
├── railway.json              # Railway config
└── tests/                    # Test suite
```

## Testing

Run tests:
```bash
pytest
```

Test coverage includes:
- Authentication
- Database operations
- API endpoints
- Analytics calculations
- Security features

## Development

### Code Quality Standards
- SOLID principles enforced
- Type hints required
- Comprehensive docstrings
- Inline comments for complex logic
- No commits without tests passing

### Adding New Features
1. Follow SOLID principles
2. Add comprehensive documentation
3. Include unit tests
4. Update API documentation
5. Test integration with frontend

## Security

- OAuth-only authentication (no passwords)
- User data isolation
- Internal database network (Railway)
- Session management
- Environment variable protection
- SQL injection prevention via parameterized queries

## Health Monitoring

- `/health` - Database connectivity check
- `/analytics-health` - User data access validation
- Status codes: 200 (healthy), 500 (error), 302 (redirect)

## Version History

- **v0.5.1-stable**: Material Design 3 implementation complete
- **Current**: API-only backend for Flutter frontend

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Follow SOLID principles and code quality standards
4. Add tests and documentation
5. Commit changes
6. Push to branch
7. Open Pull Request

## License

MIT License - See LICENSE file for details.

## Support

For issues and questions:
- **GitHub Issues**: https://github.com/alsophocus/mood-tracker-app-backend/issues
- **Frontend Repository**: https://github.com/alsophocus/mood-tracker-app-frontend
