#!/bin/bash

# Start Redis server in background
redis-server --daemonize yes

# Wait for Redis to start
sleep 2

# Navigate to Django project directory
cd /app/funATI

# Run Django migrations
python3 manage.py migrate

# Clear and collect static files
rm -rf /app/funATI/staticfiles/*
mkdir -p /app/funATI/staticfiles

# Collect static files with clear option
python3 manage.py collectstatic --noinput --clear --verbosity=1

# Set proper permissions for static files
chown -R www-data:www-data /app/funATI/staticfiles/
chmod -R 755 /app/funATI/staticfiles/

# Debug: List static files structure
echo "=== Static files structure ==="
ls -la /app/funATI/staticfiles/
echo "=== CSS files ==="
find /app/funATI/staticfiles/ -name "*.css" -type f
echo "=== JS files ==="
find /app/funATI/staticfiles/ -name "*.js" -type f
echo "=== Asset files ==="
find /app/funATI/staticfiles/ -name "*.png" -o -name "*.jpg" -o -name "*.svg" -type f

# Create superuser if it doesn't exist (optional)
python3 manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Start Daphne (ASGI server) in background for WebSockets and Django
echo "Starting Daphne server..."
cd /app/funATI

# Set Django settings and Python path
export DJANGO_SETTINGS_MODULE=funATI.settings
export PYTHONPATH=/app/funATI:$PYTHONPATH

# Debug: Show current directory and Python path
echo "Current directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "Django settings: $DJANGO_SETTINGS_MODULE"

# Test Django setup
echo "Testing Django setup..."
python3 -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'funATI.settings')
django.setup()
print('Django setup successful')
print('Available apps:', [app.name for app in django.apps.apps.get_app_configs()])
" || {
    echo "Django setup failed, trying alternative..."
    export DJANGO_SETTINGS_MODULE=funATI.settings
}

# Test channels configuration
echo "Testing Channels configuration..."
python3 -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'funATI.settings')
django.setup()
from django.conf import settings
print('ASGI_APPLICATION:', getattr(settings, 'ASGI_APPLICATION', 'Not configured'))
print('CHANNEL_LAYERS:', getattr(settings, 'CHANNEL_LAYERS', 'Not configured'))
" || echo "Channels test failed"

# Start Daphne with proper Django environment and debug
echo "Starting Daphne with command: daphne -b 0.0.0.0 -p 8001 -v 2 funATI.asgi:application"
daphne -b 0.0.0.0 -p 8001 -v 2 funATI.asgi:application &
DAPHNE_PID=$!

echo "Daphne PID: $DAPHNE_PID"

# Wait a moment to see if Daphne starts successfully
sleep 2

# Check if Daphne process is still running
if ! kill -0 $DAPHNE_PID 2>/dev/null; then
    echo "❌ Daphne failed to start, trying alternative method..."
    
    # Try to start with Django's development server
    echo "🔄 Starting with Django runserver..."
    python3 manage.py runserver 0.0.0.0:8001 --verbosity=2 &
    DAPHNE_PID=$!
    
    sleep 3
    if ! kill -0 $DAPHNE_PID 2>/dev/null; then
        echo "❌ Both Daphne and runserver failed!"
        echo "🔍 Checking Python and Django status..."
        python3 --version
        python3 -c "import django; print('Django version:', django.get_version())"
        python3 -c "import channels; print('Channels version:', channels.__version__)"
        exit 1
    else
        echo "✅ Django runserver started successfully"
    fi
else 
    echo "✅ Daphne started successfully"
fi

# Wait for Daphne to start
sleep 3

# Check if Daphne is running
if kill -0 $DAPHNE_PID 2>/dev/null; then
    echo "Daphne started successfully on port 8001"
else
    echo "Failed to start Daphne"
    exit 1
fi

# Start Apache in foreground (will proxy to Daphne)
echo "Starting Apache server..."
apache2ctl -DFOREGROUND 