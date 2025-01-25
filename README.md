# 📧 Email Control System

A powerful, enterprise-grade email management system built with FastAPI and Next.js, designed to handle millions of emails efficiently while maintaining excellent IP reputation.

## 🌟 Key Features

### Email Management
- **Multi-Account Integration**: Seamless support for Gmail, Outlook, and IMAP accounts
- **Smart Categorization**: AI-powered email categorization and priority sorting
- **Advanced Search**: Full-text search with filters and advanced query syntax
- **Bulk Operations**: Efficient handling of multiple emails simultaneously
- **Email Templates**: Create and manage reusable email templates

### Security & Performance
- **IP Reputation Management**: Built-in safeguards to maintain sender reputation
- **Rate Limiting**: Intelligent throttling to prevent account blocks
- **Security Features**: 2FA, JWT authentication, and role-based access control
- **Caching System**: Redis-based caching for optimal performance

### Monitoring & Analytics
- **Real-time Monitoring**: Track email delivery, opens, and engagement
- **Performance Metrics**: Detailed analytics on email campaigns and system performance
- **Audit Logs**: Comprehensive logging of all system activities
- **Health Checks**: Automated system health monitoring

## 🛠️ Technology Stack

### Backend Architecture
- **Framework**: FastAPI with Python 3.11
- **Database**: PostgreSQL 15 with SQLAlchemy ORM
- **Caching**: Redis 7
- **Task Queue**: Celery with Flower monitoring
- **Authentication**: JWT with OAuth2
- **Email Processing**: MIME, SMTP, IMAP protocols
- **API Docs**: OpenAPI (Swagger) & ReDoc

### Frontend Architecture
- **Framework**: Next.js 14 with TypeScript
- **State Management**: Zustand & React Query
- **UI Components**: Tailwind CSS & Headless UI
- **Forms**: React Hook Form with Zod validation
- **Charts**: Recharts for analytics
- **Testing**: Jest & React Testing Library

## 🚀 Quick Start

### Prerequisites
```bash
# Required software
Python 3.11+
Node.js 18+
PostgreSQL 15+
Redis 7+
Docker & Docker Compose (optional)
```

### Backend Setup

1. Create and activate virtual environment:
```bash
# Windows
cd backend
python -m venv venv
venv\Scripts\activate

# Linux/MacOS
cd backend
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pre-commit install
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configurations
```

4. Initialize database:
```bash
alembic upgrade head
python -m app.initial_data  # Create initial data
```

5. Start the backend:
```bash
# Development
uvicorn app.main:app --reload

# Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment:
```bash
cp .env.example .env.local
# Edit .env.local with your configurations
```

3. Start the frontend:
```bash
# Development
npm run dev

# Production
npm run build
npm start
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale workers
docker-compose up -d --scale celery_worker=3
```

## 📊 System Architecture

```mermaid
graph TD
    A[Client] --> B[Next.js Frontend]
    B --> C[FastAPI Backend]
    C --> D[PostgreSQL]
    C --> E[Redis Cache]
    C --> F[Celery Workers]
    F --> G[Email Providers]
    F --> H[Background Tasks]
```

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test categories
pytest -m unit  # Unit tests
pytest -m integration  # Integration tests
pytest -m e2e  # End-to-end tests
```

### Frontend Tests
```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

## 📈 Monitoring & Maintenance

### Health Checks
- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:3000/api/health`
- Database: `http://localhost:8000/health/db`
- Redis: `http://localhost:8000/health/redis`

### Monitoring Tools
- Celery Flower: `http://localhost:5555`
- Prometheus Metrics: `http://localhost:8000/metrics`
- Application Logs: `docker-compose logs -f`

## 🔧 Configuration

The system can be configured using environment variables. Key configurations:

```env
# Application
DEBUG=true
API_V1_STR=/api/v1
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Email Limits
MAX_EMAILS_PER_DAY=1000
MAX_RECIPIENTS_PER_EMAIL=50
```

## 📚 API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

## 🔐 Security Features

- JWT Authentication
- OAuth2 Integration
- Rate Limiting
- CORS Protection
- SQL Injection Prevention
- XSS Protection
- CSRF Protection
- Security Headers
- Input Validation
- Output Sanitization

## 🌍 Scaling Considerations

- Horizontal Scaling
  - Stateless API Design
  - Redis for Session Storage
  - Load Balancing Support
  
- Performance Optimization
  - Query Optimization
  - Caching Strategies
  - Background Processing
  - Connection Pooling

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Commit Guidelines
```
feat: Add new feature
fix: Bug fix
docs: Update documentation
style: Code style update
refactor: Code refactoring
test: Add tests
chore: Update build tasks
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Support

- Documentation: [docs/](docs/)
- Issue Tracker: [GitHub Issues](https://github.com/yourusername/email-control-system/issues)
- Security: [SECURITY.md](SECURITY.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)

## 🙏 Acknowledgments

- FastAPI
- Next.js
- SQLAlchemy
- And all other open-source libraries used in this project

---
Built with ❤️ by Your Team
