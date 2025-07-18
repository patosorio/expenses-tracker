# Expense Tracking Application

Full-stack application for expense tracking with document processing capabilities.

## Tech Stack

- Frontend: Next.js 14 (TypeScript)
- Backend: FastAPI (Python)
- Database: PostgreSQL
- Authentication: Firebase
- Storage: Firebase Storage
- Caching: Redis
- ML/AI: Google Gemini API, scikit-learn

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
fastapi dev src/main.py
```

### Frontend

```bash
cd client
npm install
npm run dev
```

### Environment Variables

Required environment variables in `.env`:

```
# Backend
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
FIREBASE_SERVICE_ACCOUNT=path/to/service-account.json
GOOGLE_API_KEY=your_gemini_api_key
REDIS_URL=redis://localhost:6379

# Frontend
NEXT_PUBLIC_FIREBASE_CONFIG=your_firebase_config
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Features

- User authentication and authorization
- Expense tracking and categorization
- Document processing (receipts, invoices, tickets)
- Budget management
- Financial forecasting
- Data visualization
- Export/import capabilities

## API Documentation

API documentation available at `/docs` or `/redoc` when running the backend server.

## Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd client
npm test
```

## License

MIT