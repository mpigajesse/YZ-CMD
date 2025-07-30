#!/bin/bash
# Build script for Vercel deployment

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create a simple wsgi.py file for Vercel
cat > vercel_wsgi.py << EOF
import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Import Django and create the WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
EOF 