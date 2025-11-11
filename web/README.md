# OsMEN Web Dashboard

No-code web interface for managing the OsMEN AI assistant system.

## Features

### v1.7.0 Phase I: Dashboard Foundation ✅

- **FastAPI Backend**: Async web server with session-based authentication
- **HTMX Frontend**: Simple, no-JavaScript-heavy interface
- **Live Log Streaming**: Real-time system logs via Server-Sent Events
- **System Status**: Real-time monitoring of agents, services, and resources
- **Responsive Design**: Mobile-friendly with TailwindCSS
- **Secure Authentication**: Session-based login with bcrypt password hashing

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (optional):
```bash
export WEB_SECRET_KEY="your-secret-key-here"
export WEB_USERNAME="admin"
export WEB_PASSWORD_HASH="<bcrypt hash of your password>"
export WEB_PORT="8000"
export WEB_HOST="0.0.0.0"
```

3. Generate password hash:
```bash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"
```

## Usage

### Start the Dashboard

```bash
cd /path/to/OsMEN
uvicorn web.main:app --host 0.0.0.0 --port 8000 --reload
```

Or run with Python directly:
```bash
python3 -m web.main
```

### Access the Dashboard

Open your browser to: http://localhost:8000

Default credentials:
- Username: `admin`
- Password: `admin`

**⚠️ Change the default password in production!**

## Features

### Dashboard Page

- **System Overview**: Agent health, service status, resource usage
- **Live Logs**: Real-time log streaming with auto-scroll
- **Quick Actions**: One-click buttons for common tasks
- **Real-time Updates**: Auto-refresh every 30 seconds

### API Endpoints

- `GET /` - Root (redirects to dashboard or login)
- `GET /login` - Login page
- `POST /login` - Handle login
- `GET /logout` - Logout
- `GET /dashboard` - Main dashboard
- `GET /api/status` - System status JSON
- `GET /api/agents` - Agent health JSON
- `GET /api/services` - Service health JSON
- `GET /logs/stream` - Live log streaming (SSE)

## Architecture

```
web/
├── __init__.py          # Package initialization
├── main.py              # FastAPI application
├── auth.py              # Authentication module
├── status.py            # System status monitoring
├── templates/           # Jinja2 templates
│   ├── base.html        # Base template
│   ├── login.html       # Login page
│   └── dashboard.html   # Dashboard page
└── static/              # Static assets
    ├── styles.css       # Custom CSS
    └── app.js           # Client-side JavaScript
```

## Security

- Session-based authentication (not JWT for simplicity)
- Bcrypt password hashing
- CSRF protection via Starlette middleware
- HTTPS recommended in production
- Environment variable configuration

## Development

### Run in Development Mode

```bash
uvicorn web.main:app --reload --log-level debug
```

### Watch for Changes

The `--reload` flag automatically reloads on file changes.

### Debug Mode

Set environment variable for verbose logging:
```bash
export DEBUG=1
```

## Production Deployment

### Using Uvicorn

```bash
uvicorn web.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn

```bash
gunicorn web.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker

```bash
docker build -t osmen-web .
docker run -p 8000:8000 osmen-web
```

## Configuration

All configuration via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB_SECRET_KEY` | `dev-secret-key-change-in-production` | Session secret key |
| `WEB_USERNAME` | `admin` | Default username |
| `WEB_PASSWORD_HASH` | `<hash of 'admin'>` | Bcrypt password hash |
| `WEB_PORT` | `8000` | Server port |
| `WEB_HOST` | `0.0.0.0` | Server host |

## Roadmap

### v1.7.0 Phase J: Agent Configuration UI (Next)
- [ ] Visual agent setup wizard
- [ ] Configuration editors (no YAML/JSON)
- [ ] Integration toggles
- [ ] Preference settings
- [ ] Semester setup wizard

### v1.7.0 Phase K: Daily Digest & Review
- [ ] Daily summary display
- [ ] Batch approval interface
- [ ] Activity timeline
- [ ] Performance metrics

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Session Errors

Clear browser cookies or use incognito mode.

### Module Not Found

```bash
pip install -r requirements.txt
```

## License

Same as OsMEN project.
