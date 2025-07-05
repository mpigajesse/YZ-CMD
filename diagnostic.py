#!/usr/bin/env python3
"""
Diagnostic simple de l'API
"""

import os
import sys
import django
import traceback

# Configuration Django
sys.path.append('/workspaces/YZ-CMD')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from kpis.views import performance_operateurs_data

def test_simple():
    factory = RequestFactory()
    user = User.objects.first() or User.objects.create_user('test', 'test@example.com', 'test')
    
    request = factory.get('/kpis/performance-operateurs-data/', {'period': 'today'})
    request.user = user
    
    try:
        response = performance_operateurs_data(request)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Content: {response.content.decode('utf-8')}")
    except Exception as e:
        print(f"Exception: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()
