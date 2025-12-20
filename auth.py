#!/usr/bin/python3
'''
Scripts which handle the authentication process and validation of token
on the resource server side
'''
import secrets
import hashlib
import base64
import jwt
from fastapi import HTTPException, Depends, Request
import os
from dotenv import load_dotenv

load_dotenv(".env")

#Will move it to env later on
with open(os.environ.get("PUBLIC_KEY_PATH"), "rb") as f:
    PUBLIC_KEY = f.read()

ALGORITHM = os.environ.get("ALGORITHM")
AUDIENCE = os.environ.get("AUDIENCE")
RESOURCE_API_BASE = os.environ.get("RESOURCE_API_BASE")
INTERNAL_SHARED_SECRET = os.environ.get("INTERNAL_SHARED_SECRET")

def generate_pkce_pair():
    '''
    Function which generates verifier and challenge to be used on request
    '''
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
    hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge

def check_current_user(request):
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
            options={"require": ["exp", "sub"]}
        )
    except jwt.ExpiredSignatureError:
        print("JWT Expired Signature")
        return None
    except jwt.InvalidTokenError:
        print("JWT Invalid Token")
        return None

    return {
        "user_id": payload["sub"],
        "role": payload["role"],
        "client_id": payload.get("client_id")
    }

def admin_required(user=Depends(check_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def admin_required_api(request: Request):
    user = check_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user

def user_level(request: Request, user_level=Depends(check_current_user)):
    user = check_current_user(request)
    if user["role"] != "user":
        raise HTTPException(status_code=403, detail="Access Denied! Only User access allowed")


def verify_internal_secret(request):
    secret = request.headers.get("X-Internal-Secret")
    if secret != INTERNAL_SHARED_SECRET:
        raise HTTPException(status_code=404)