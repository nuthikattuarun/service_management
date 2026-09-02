# Quick Deployment Checklist

## Pre-Deployment (Local)

- [ ] All tests pass locally
- [ ] Database migrations complete
- [ ] `python manage.py check` passes
- [ ] `python manage.py collectstatic --no-input` succeeds
- [ ] `.env` file NOT committed to git
- [ ] `requirements.txt` updated with all dependencies

## GitHub Setup

```bash
cd d:\service_management\service_management

# Initialize and commit
git init
git add .
git commit -m "Initial commit: Ready for production deployment"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/service-management.git
git branch -M main
git push -u origin main
```

## Render Setup

1. Go to https://render.com → Sign in
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Select "service-management" repo

### Configure in Render:

**Name:** service-management-api
**Branch:** main
**Root Directory:** (leave empty, uses repository root)

**Build Command:**
```
cd backend && pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
```

**Start Command:**
```
cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

**Environment Variables:** Add from `.env.example`
```
DEBUG=False
SECRET_KEY=<new-strong-key>
ALLOWED_HOSTS=<your-render-app>.onrender.com
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=<from-neon>
DB_HOST=<your-neon-host>
DB_PORT=5432
PGSSLMODE=require
JWT_SECRET_KEY=<new-strong-key>
JWT_ACCESS_TOKEN_LIFETIME_DAYS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

## After Deployment

- [ ] Check build logs in Render
- [ ] Access: `https://<your-app>.onrender.com`
- [ ] Check API: `https://<your-app>.onrender.com/api/docs/`
- [ ] Check Admin: `https://<your-app>.onrender.com/admin/`
- [ ] Check Dashboard: `https://<your-app>.onrender.com/ui/dashboard/`
- [ ] Test login endpoint
- [ ] Verify static files load
- [ ] Monitor logs for errors

## Files Changed

### New Files Created:
- `.env.example` - Environment variables template
- `render.yaml` - Render deployment config
- `Procfile` - Alternative deployment config
- `build.sh` - Build script
- `DEPLOYMENT.md` - Full deployment guide
- `DEPLOYMENT_QUICK.md` - This file

### Modified Files:
- `requirements.txt` - Added Gunicorn, WhiteNoise, dj-database-url
- `config/settings.py` - Production settings, static files, middleware
- `.gitignore` - Comprehensive ignore rules

### Not Changed (Existing Functionality Preserved):
- All API endpoints
- All Django templates
- All models and migrations
- All authentication logic
- All existing apps

## Important Notes

1. **Never commit .env** - Always use environment variables in production
2. **Change SECRET_KEY** - Generate a new strong key for production
3. **Change JWT_SECRET_KEY** - Generate a new strong key for production
4. **Set DEBUG=False** - Never run production with DEBUG=True
5. **Use HTTPS** - Automatic with Render (configured in settings.py)
6. **Monitor logs** - Check Render logs regularly for issues

## Rollback

If deployment fails:
1. Push a fix to GitHub
2. Render will auto-rebuild
3. Or manually redeploy in Render dashboard
4. Database changes are NOT rolled back automatically

## Local Commands Reference

```bash
# Development
python manage.py runserver

# Production testing
python manage.py check
python manage.py collectstatic --no-input

# Database
python manage.py migrate
python manage.py makemigrations

# Admin
python manage.py createsuperuser

# Shell
python manage.py shell

# Requirements
pip install -r requirements.txt
pip freeze > requirements.txt
```
