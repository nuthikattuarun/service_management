# Service Management - Deployment Guide

## Project Overview
This is a Django Service Management application with:
- **Backend**: Django 6.1 with REST API (DRF + Spectacular)
- **Database**: Neon PostgreSQL (production)
- **Frontend**: Django Templates with static files
- **Authentication**: JWT tokens + Session-based

## Production Deployment Architecture

### Files Modified for Deployment
1. **requirements.txt** - Added Gunicorn, WhiteNoise, dj-database-url
2. **config/settings.py** - Production security settings, static files, WhiteNoise middleware
3. **.gitignore** - Comprehensive ignores for secrets, virtual env, cache
4. **.env.example** - Template for environment variables (NO SECRETS)
5. **render.yaml** - Render deployment configuration
6. **Procfile** - Alternative deployment configuration
7. **build.sh** - Automated build script

## Local Development Setup

### Prerequisites
- Python 3.8+
- PostgreSQL (or connection to Neon)
- Git

### Install Dependencies
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Configure Environment Variables
1. Copy .env.example to .env
```bash
copy .env.example .env
```

2. Update .env with your actual values:
```
DEBUG=True
SECRET_KEY=your-dev-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=your-neon-password
DB_HOST=your-neon-host.neon.tech
DB_PORT=5432
```

### Run Migrations
```bash
python manage.py migrate
```

### Collect Static Files
```bash
python manage.py collectstatic --no-input
```

### Run Development Server
```bash
python manage.py runserver
```

Access at: http://127.0.0.1:8000/

## Production Deployment (Render)

### Prerequisites
- GitHub account with repository containing this code
- Render account (https://render.com)
- Neon PostgreSQL database (already configured)

### Step 1: Prepare GitHub Repository

```bash
# Initialize git (if not already)
cd d:\service_management\service_management
git init

# Configure git
git config user.email "your-email@example.com"
git config user.name "Your Name"

# Add all files
git add .

# Commit
git commit -m "Initial commit: Ready for production deployment"

# Create repository on GitHub and push
git remote add origin https://github.com/your-username/service-management.git
git branch -M main
git push -u origin main
```

### Step 2: Connect Render to GitHub

1. Go to https://render.com
2. Sign in to your account
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Select the repository "service-management"
6. Render will auto-detect the build and start commands

### Step 3: Configure Environment Variables in Render

In Render dashboard, go to your Web Service → Environment:

Add these environment variables (copy values from your .env):
```
DEBUG=False
SECRET_KEY=<generate-a-strong-key>
ALLOWED_HOSTS=your-render-app.onrender.com,www.your-render-app.onrender.com
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=<your-neon-password>
DB_HOST=<your-neon-host.neon.tech>
DB_PORT=5432
PGSSLMODE=require
JWT_SECRET_KEY=<generate-a-strong-key>
JWT_ACCESS_TOKEN_LIFETIME_DAYS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

### Step 4: Configure Build and Start Commands

**Build Command:**
```bash
cd backend && pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
```

**Start Command:**
```bash
cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

### Step 5: Deploy

1. Render will automatically deploy when you push to GitHub
2. You can manually trigger a deployment in Render dashboard
3. Monitor logs in Render dashboard

## After Deployment Checklist

### 1. Verify API Endpoints
- [ ] Swagger API Docs: `https://your-app.onrender.com/api/docs/`
- [ ] ReDoc Documentation: `https://your-app.onrender.com/api/redoc/`
- [ ] API Schema: `https://your-app.onrender.com/api/schema/`

### 2. Test Authentication Endpoints
```bash
# Postman or curl

# Register
POST https://your-app.onrender.com/api/auth/register/
Body: {
  "email": "test@example.com",
  "password": "securepass123",
  "first_name": "Test",
  "last_name": "User"
}

# Login
POST https://your-app.onrender.com/api/auth/login/
Body: {
  "email": "test@example.com",
  "password": "securepass123"
}

# Response should include access and refresh tokens
```

### 3. Test Dashboard/UI
- [ ] Homepage: `https://your-app.onrender.com/`
- [ ] Login: `https://your-app.onrender.com/ui/login/`
- [ ] Dashboard (after login): `https://your-app.onrender.com/ui/dashboard/`
- [ ] Verify static files load (CSS, JS)

### 4. Test Admin Panel
- [ ] Admin: `https://your-app.onrender.com/admin/`
- [ ] Create a superuser if needed:
  ```bash
  python manage.py createsuperuser
  ```

### 5. Test Database Connection
- Verify migrations ran: Check /api/ endpoints return data
- Verify Neon connection is secure (SSL)

### 6. Test File Uploads (if applicable)
- Upload attachment in request detail
- Verify file is stored correctly

### 7. Monitor Performance
- Check Render logs for errors
- Monitor response times
- Check for 404 errors

## Troubleshooting

### Issue: 500 Internal Server Error
**Solution:**
1. Check Render logs: `Logs` tab in Render dashboard
2. Ensure all environment variables are set
3. Ensure database migrations completed: Check build output
4. Ensure SECRET_KEY is strong and unique

### Issue: 404 Not Found on Static Files
**Solution:**
1. Verify collectstatic ran: Check build logs
2. Check STATIC_ROOT is set: Already configured in settings.py
3. Check WhiteNoise middleware is active: Already added to MIDDLEWARE

### Issue: Database Connection Failed
**Solution:**
1. Verify DB_HOST, DB_USER, DB_PASSWORD are correct
2. Ensure Neon IP allows Render (check Neon IP allowlist)
3. Verify PGSSLMODE=require is set
4. Test connection locally first

### Issue: Migration Fails
**Solution:**
1. Ensure no existing migrations conflict
2. Run migrations locally first to test
3. Check migration files are in git

## Production Security Settings

The following security settings are automatically enabled when DEBUG=False:

- SECURE_SSL_REDIRECT = True (Enforces HTTPS)
- SESSION_COOKIE_SECURE = True (Cookies only over HTTPS)
- CSRF_COOKIE_SECURE = True (CSRF cookies only over HTTPS)
- SECURE_HSTS_SECONDS = 31536000 (1 year HSTS header)
- SECURE_BROWSER_XSS_FILTER = True (XSS protection)
- SECURE_CONTENT_SECURITY_POLICY (CSP headers)

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| DEBUG | Enable debug mode | False (production), True (dev) |
| SECRET_KEY | Django secret key | django-insecure-... |
| ALLOWED_HOSTS | Allowed domains | your-app.onrender.com |
| DB_NAME | Database name | neondb |
| DB_USER | Database user | neondb_owner |
| DB_PASSWORD | Database password | (from Neon) |
| DB_HOST | Database host | ep-....neon.tech |
| DB_PORT | Database port | 5432 |
| PGSSLMODE | SSL mode | require |
| JWT_SECRET_KEY | JWT signing key | (generate unique) |
| JWT_ACCESS_TOKEN_LIFETIME_DAYS | Access token expiry | 1 |
| JWT_REFRESH_TOKEN_LIFETIME_DAYS | Refresh token expiry | 7 |

## Production Deployment Commands

### Build (runs on Render automatically)
```bash
cd backend && pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
```

### Start (runs on Render automatically)
```bash
cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

### Local Testing (use development server)
```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

## Next Steps After Deployment

1. **Monitor in Production**
   - Watch Render logs for errors
   - Monitor API response times
   - Check database performance

2. **Set Up Logging**
   - Consider adding Sentry for error tracking
   - Set up email alerts for critical errors

3. **Performance Optimization** (Future)
   - Add Redis caching
   - Implement CDN for static files
   - Database query optimization

4. **Scaling** (When Needed)
   - Upgrade Render plan
   - Add read replicas in Neon
   - Implement load balancing

## Support

For issues or questions:
- Render docs: https://render.com/docs
- Django docs: https://docs.djangoproject.com/
- Neon docs: https://neon.tech/docs
- DRF docs: https://www.django-rest-framework.org/
