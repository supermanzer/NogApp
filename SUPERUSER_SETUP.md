# Superuser Management for Production Deployments

## Overview

Your Django application now automatically creates a superuser during deployment using environment variables. This ensures admin access is set up automatically without needing manual intervention.

## How It Works

### Automatic Superuser Creation

When your application starts (via Docker Compose), the `create_superuser` management command runs automatically and:

1. Checks for required environment variables:
   - `DJANGO_SUPERUSER_USERNAME`
   - `DJANGO_SUPERUSER_EMAIL`
   - `DJANGO_SUPERUSER_PASSWORD`

2. Validates that all variables are set
3. Checks if the superuser already exists (prevents duplicate creation)
4. Creates the superuser with the provided credentials
5. Logs the result to stdout

### Setup Instructions

#### 1. Create Your `.env` File

Copy the provided `.env.example` to `.env`:

```bash
cp .env.example .env
```

#### 2. Edit `.env` with Your Credentials

```bash
# Admin Credentials (required for first deployment)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com
DJANGO_SUPERUSER_PASSWORD=your-strong-password-here

# Other required settings
DJANGO_SECRET_KEY=your-secret-key-here-change-in-production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

⚠️ **Security Important**: 
- Never commit `.env` to version control
- Use a strong password for production
- Change `DJANGO_SECRET_KEY` to a unique value
- Set `DJANGO_DEBUG=False` in production

#### 3. Deploy/Restart

When you start the application, the superuser is automatically created:

```bash
docker compose up -d
```

Check the logs to confirm:

```bash
docker compose logs django | grep -i "superuser\|admin"
```

You should see:

```
Successfully created superuser "admin" with email "admin@yourdomain.com"
```

Or if it already exists:

```
Superuser with username "admin" already exists. Skipping creation.
```

## Accessing the Admin Panel

Once deployed, access the Django admin at:

```
http://your-domain.com/admin/
```

**Login credentials:**
- Username: `DJANGO_SUPERUSER_USERNAME` (from `.env`)
- Password: `DJANGO_SUPERUSER_PASSWORD` (from `.env`)

## Changing Admin Credentials

To change the superuser credentials after deployment:

### Option 1: Via Django Shell (Quick)

```bash
docker compose exec django python manage.py shell
```

Then in the Python shell:

```python
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='admin')
user.email = 'newemail@example.com'
user.set_password('newpassword')
user.save()
exit()
```

### Option 2: Via Django Admin Panel

1. Log in to http://your-domain.com/admin/
2. Click "Users" under Authentication and Authorization
3. Click your admin username
4. Update email and/or password
5. Click "Save"

### Option 3: Using Management Command

```bash
docker compose exec django python manage.py changepassword admin
```

## Deleting and Recreating Superuser

If you need to completely recreate the superuser:

### 1. Delete the existing superuser:

```bash
docker compose exec django python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(username='admin').delete()
exit()
```

### 2. Restart the application:

```bash
docker compose down
docker compose up -d
```

The new superuser will be created automatically from your `.env` variables.

## Multiple Superusers

To create additional superuser accounts, use the interactive command:

```bash
docker compose exec django python manage.py createsuperuser
```

Then follow the prompts to create a new admin account.

## Default Credentials

If you don't set environment variables, the application uses these defaults:

- Username: `admin`
- Email: `admin@example.com`
- Password: `changeme`

⚠️ **WARNING**: Never use default credentials in production! Always set strong, unique credentials in your `.env` file.

## Troubleshooting

### "Superuser already exists" but I forgot the password

Use the `changepassword` command:

```bash
docker compose exec django python manage.py changepassword admin
```

### Admin page returns 404

Verify your URLs are configured correctly in `nog_app/urls.py`. The admin path should be:

```python
path("admin/", admin.site.urls),
```

### Can't log in even with correct credentials

1. Check that `DEBUG=False` is set (redirects to login)
2. Verify the superuser exists:

```bash
docker compose exec django python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.filter(is_superuser=True).values('username', 'email'))
exit()
```

3. Check application logs for errors:

```bash
docker compose logs django | tail -50
```

## Security Best Practices

1. **Use Strong Passwords**: Generate using a password manager or:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Separate Credentials**: Store `.env` securely, not in version control

3. **Unique Secret Key**: Generate using:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **HTTPS**: Configure SSL/TLS for production (see PRODUCTION_DEPLOYMENT.md)

5. **Regular Password Changes**: Change admin password periodically

6. **Audit Access**: Monitor Django admin logs for unauthorized access attempts

## Related Documentation

- [Django Authentication System](https://docs.djangoproject.com/en/5.2/topics/auth/)
- [Django Admin Site](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/)
- [Management Commands](https://docs.djangoproject.com/en/5.2/ref/django-admin/)
- See `PRODUCTION_DEPLOYMENT.md` for complete deployment guide
