"""
WSGI config for YZ-CMD project on Vercel.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_dir))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Import Django and create the WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application() 