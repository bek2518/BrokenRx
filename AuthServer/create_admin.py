#!/usr/bin/python3
'''
Script for creating and adding an admin to the database
No registration of admins from UI for security reasons
'''

from models.auth_db_handler import DatabaseHandler
from app.auth import hash_password
import sys
from getpass import getpass
import requests
import os
from dotenv import load_dotenv

load_dotenv(".env.auth")

MAIN_APP_BASE = os.environ.get("MAIN_APP_BASE")
INTERNAL_SHARED_SECRET = os.environ.get("INTERNAL_SHARED_SECRET")

print("Creating Admin User")

username = input("Input Admin Username:     ")
email = input("Input Admin email:       ")
password = getpass()

password_hash = hash_password(password)
print(username, email)

complete_url = f"{MAIN_APP_BASE}/registration/complete"

with DatabaseHandler() as db:
    registration = db.store_admin(username, password_hash)

    profile = {
        "user_id": registration,
        "username": username,
        "email": email,
        "is_admin": 1
    }

    headers = {"X-Internal-Secret": INTERNAL_SHARED_SECRET}
    resp = requests.post(complete_url, json=profile, headers=headers)

print(f"New admin {username} created")