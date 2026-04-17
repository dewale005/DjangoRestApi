from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[3]
SECRET_KEY = os.getenv("SECRET_KEY", "unsafe")
DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",") if os.getenv("ALLOWED_HOSTS") else []
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes"]
DATABASES = {}
