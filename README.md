# 📧 Email Control System

<div align="center">

![Email Control System](https://img.shields.io/badge/Email-Control_System-blue?style=for-the-badge&logo=gmail)

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)

A powerful, enterprise-grade email management system that handles millions of emails while maintaining excellent IP reputation.

[Getting Started](#-quick-start) •
[Features](#-key-features) •
[Documentation](#-documentation) •
[Tech Stack](#%EF%B8%8F-technology-stack) •
[Contributing](#-contributing)

</div>

---

## ✨ Why Email Control System?

- 🚀 **High Performance**: Handles millions of emails efficiently
- 🔒 **Enterprise Security**: Bank-grade security with 2FA and encryption
- 🎯 **Smart Management**: AI-powered categorization and priority sorting
- 📊 **Rich Analytics**: Detailed insights into email performance
- 🔄 **Seamless Integration**: Works with Gmail, Outlook, and IMAP
- ⚡ **Real-time Updates**: Instant notifications and live updates
- 🛡️ **IP Protection**: Built-in safeguards for sender reputation

## 🌟 Key Features

### 📨 Email Management
- **Multi-Account Support**
  - Gmail, Outlook, and IMAP integration
  - Unified inbox across all accounts
  - Account-specific settings and rules
  
- **Smart Organization**
  - AI-powered categorization
  - Priority inbox with smart sorting
  - Custom folders and labels
  - Advanced search with filters

- **Bulk Operations**
  - Mass email processing
  - Template management
  - Scheduled sending
  - Batch updates

### 🔐 Security & Performance

- **Authentication & Authorization**
  - Two-factor authentication (2FA)
  - Role-based access control (RBAC)
  - JWT with secure refresh tokens
  - OAuth2 integration

- **Performance Optimization**
  - Redis caching
  - Connection pooling
  - Query optimization
  - Rate limiting

- **Data Protection**
  - End-to-end encryption
  - Data backup and recovery
  - Audit logging
  - GDPR compliance

## 🚀 Quick Start

### Prerequisites

Make sure you have the following installed:

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### One-Click Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/email-control-system.git
cd email-control-system

# Run setup script
./setup.sh  # Linux/MacOS
setup.bat   # Windows
```

### Manual Setup

<details>
<summary>Backend Setup</summary>

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
alembic upgrade head
python -m app.initial_data

# Start server
uvicorn app.main:app --reload
```
</details>

<details>
<summary>Frontend Setup</summary>

```bash
# Install dependencies
cd frontend
npm install

# Setup environment
cp .env.example .env.local
# Edit .env.local with your settings

# Start development server
npm run dev
```
</details>

<details>
<summary>Docker Setup</summary>

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale workers
docker-compose up -d --scale worker=3
```
</details>

## 📚 Documentation

- [API Documentation](http://localhost:8000/docs)
- [Frontend Documentation](http://localhost:3000/docs)
- [Architecture Overview](./docs/architecture.md)
- [Development Guide](./docs/development.md)
- [Deployment Guide](./docs/deployment.md)
- [Security Guide](./docs/security.md)

## 🛠️ Technology Stack

<details>
<summary>Backend Stack</summary>

- **Core**: FastAPI, Python 3.11
- **Database**: PostgreSQL 15, SQLAlchemy, Alembic
- **Caching**: Redis 7
- **Queue**: Celery, RabbitMQ
- **Security**: JWT, OAuth2, Passlib
- **Testing**: Pytest, Coverage
</details>

<details>
<summary>Frontend Stack</summary>

- **Core**: Next.js 14, TypeScript
- **State**: Zustand, React Query
- **UI**: Tailwind CSS, Headless UI
- **Forms**: React Hook Form, Zod
- **Testing**: Jest, Testing Library
</details>

## 🔧 Configuration

### Environment Variables

<details>
<summary>Backend Configuration</summary>

```env
# Application
DEBUG=true
API_V1_STR=/api/v1
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```
</details>

<details>
<summary>Frontend Configuration</summary>

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GA_ID=your-ga-id
```
</details>

## 🧪 Testing

```bash
# Backend tests
pytest                 # Run all tests
pytest --cov=app      # With coverage
pytest -m unit        # Unit tests only

# Frontend tests
npm test              # Run all tests
npm test -- --watch   # Watch mode
```

## 📈 Monitoring

- **Health Checks**: `http://localhost:8000/health`
- **API Metrics**: `http://localhost:8000/metrics`
- **Task Queue**: `http://localhost:5555` (Flower)
- **Logs**: `docker-compose logs -f`

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)
