#!/usr/bin/python3
'''
Authentication script which handles password hashing, JWT generation and validation
'''

import hashlib
import jwt
import time
import uuid
from passlib.context import CryptContext
import secrets
import base64
import os
from dotenv import load_dotenv

load_dotenv(".env.auth")

algorithm = os.environ.get("ALGORITHM")
issuer = os.environ.get("ISSUER")
audience = os.environ.get("AUDIENCE")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Reads the private key, will move it to env
# generate the private and public key to be used, keep the private key in the authorization
# server and the public key in the resource server
with open(os.environ.get("PRIVATE_KEY_PATH"), "rb") as f:
    PRIVATE_KEY = f.read()


def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def verify_pkce(verifier: str, challenge: str) -> bool:
    if not verifier or not challenge:
        return False

    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    computed_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    return secrets.compare_digest(computed_challenge, challenge)


def create_access_token(user_id, role, client_id):
    '''
    Function which generates jwt access token 
    '''
    now = int(time.time())
    payload = {
        "iss": issuer,
        "aud": audience,
        "sub": str(user_id),
        "role": role,
        "client_id": client_id,
        "scope": "user",
        "iat": now,
        "exp": now + 3600,
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm=algorithm)