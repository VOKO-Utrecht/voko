import os
import sys

# Add webapp to path so Django can find the apps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# pytest-django will handle Django setup automatically using the
# DJANGO_SETTINGS_MODULE from pyproject.toml
