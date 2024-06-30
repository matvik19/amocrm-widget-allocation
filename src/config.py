from dotenv import load_dotenv
import os

load_dotenv()

ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
SUBDOMAIN = os.environ.get("SUBDOMAIN")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
CLIENT_ID = os.environ.get("CLIENT_ID")
CODE = os.environ.get("CODE")
REDIRECT_URL = os.environ.get("REDIRECT_URL")

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

