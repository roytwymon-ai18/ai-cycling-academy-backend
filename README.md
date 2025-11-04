# AI Cycling Academy - Backend API

Flask backend for AI Cycling Academy - AI-powered cycling coaching platform.

## Features

- User authentication and profile management
- Ride upload and parsing (.fit, .gpx, .tcx)
- AI coaching chat with context awareness
- Performance analytics and insights
- Training goals tracking
- Dashboard data aggregation

## Deployment

### Railway (Recommended)

1. Push to GitHub
2. Connect repository to Railway
3. Set environment variables:
   - `FLASK_ENV=production`
   - `SECRET_KEY=your-secret-key-here`
   - `OPENAI_API_KEY=your-openai-key` (if using OpenAI)
4. Deploy automatically

### Environment Variables

- `FLASK_ENV` - Set to `production` for production deployment
- `SECRET_KEY` - Flask secret key for session management
- `PORT` - Port to run on (Railway sets this automatically)
- `OPENAI_API_KEY` - OpenAI API key for AI coaching (optional, Manus AI can be used instead)

## Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python3 src/main.py
```

## API Endpoints

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/dashboard` - Dashboard data
- `POST /api/upload` - Upload ride file
- `GET /api/rides` - Get user rides
- `POST /api/coaching/chat` - AI coaching chat
- `GET /api/analytics` - Performance analytics
- `GET /api/training-plans/*` - Training plan management

## Database

SQLite database stored in `src/database/app.db`. Automatically created on first run.

## Production Notes

- Uses gunicorn WSGI server
- 4 workers for concurrent requests
- 120 second timeout for long-running requests
- Automatic restart on failure
- CORS enabled for frontend access

