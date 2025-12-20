#!/usr/bin/python3

'''
Fast API to query the sqlite database and return authorization server
'''
import logging
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from models.auth_db_handler import DatabaseHandler
from app.auth import hash_password, verify_password, create_access_token, verify_pkce
import secrets
import time
from starlette.middleware.sessions import SessionMiddleware
import requests
import os
from dotenv import load_dotenv

load_dotenv(".env.auth")

MAIN_APP_BASE = os.environ.get("MAIN_APP_BASE")
INTERNAL_SHARED_SECRET = os.environ.get("INTERNAL_SHARED_SECRET")

# Initialize the Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="BrokenRx Auth Server API")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("MIDDLEWARE_SECRET_KEY"),
    https_only=False
)

SessionMiddleware(
    app,
    secret_key=os.environ.get("SECRET_KEY"),
    session_cookie=os.environ.get("oauth_session")
)

templates = Jinja2Templates(directory="app/templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with DatabaseHandler() as db:
    db.init_oauth_client()

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(
    request: Request,
    username = Form(...),
    password = Form(...),
    email = Form(...)
    ):
    complete_url = f"{MAIN_APP_BASE}/registration/complete"
    password_hash = hash_password(password)

    with DatabaseHandler() as db:
        registration = db.store_users(username, password_hash)

    if registration == "username exists":
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already exists"},
            status_code=400
        )

    if registration == "Error":
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Error creating user. Try Again"},
            status_code=400
        )
    profile = {
        "user_id": registration,
        "username": username,
        "email": email,
        "is_admin": 0
    }

    headers = {"X-Internal-Secret": INTERNAL_SHARED_SECRET}
    resp = requests.post(complete_url, json=profile, headers=headers)
    return RedirectResponse("/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(
    request: Request,
    username = Form(...),
    password = Form(...)
):
    with DatabaseHandler() as db:
        user = db.retrieve_users(username)

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=401
        )
    stored_hash = str(user[2])
    if not verify_password(password, stored_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=401
        )
    request.session["user_id"] = user[0]
    request.session["role"] = user[3]

    original_query = request.session.pop("original_authorize_query", None)
    if original_query:
        redirect_url = f"/authorize?{original_query}"
        return RedirectResponse(redirect_url, status_code=302)

    return RedirectResponse("/authorize", status_code=302)

@app.get("/authorize")
def authorize(request: Request):
    
    query_string = str(request.url.query)

    if "user_id" not in request.session:
        request.session["original_authorize_query"] = query_string
        return RedirectResponse("/login", status_code=302)


    user_id = request.session.get("user_id")
    
    params = request.query_params
    client_id = params.get("client_id")
    redirect_uri = params.get("redirect_uri")
    code_challenge = params.get("code_challenge")
    code = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + 600
    
    with DatabaseHandler() as db:
        client = db.oauth_client(client_id) 
    # FIX FOR REDIRECT
    '''
    # Fix No 1: not processing the request entirely
    if client[2] != redirect_uri:
        raise HTTPException(status_code=400, detail="Invalid Redirect URL")
    '''
    
    '''
    # Fix No 2: Replacing the redirect_uri using the whitelist database
    redirect_uri = client[2]
    '''
    if not client_id:
        raise HTTPException(status_code=400, detail="Invalid client")
    request.session["oauth_request"] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
    }

    with DatabaseHandler() as db:
        db.store_authorization_codes(code, user_id, client_id, redirect_uri, code_challenge, expires_at)
    
    redirect = f"{redirect_uri}?code={code}"

    return RedirectResponse(redirect, status_code=302)

@app.post("/token")
def token(
    code = Form(...),
    code_verifier = Form(None),
    client_id = Form(...)
    ):

    with DatabaseHandler() as db:
        auth_code = db.retrieve_authorization_code(code)

    if not auth_code or auth_code == "Invalid Code":
        raise HTTPException(status_code=400, detail="Invalid code")

    if not verify_pkce(code_verifier or "", auth_code[4]):
        raise HTTPException(status_code=400, detail="PKCE failed")

    # FIX FOR CODE REUSE

    # Removes the authorization code from the database once it has been retrieved preventing
    # future use and avoids the code reuse
    with DatabaseHandler() as db:
        db.remove_authorization_code(code)


    user_id=auth_code[1]

    with DatabaseHandler() as db:
        user = db.retrieve_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    role = user[3]

    token = create_access_token(
        user_id=user_id,
        role=role,
        client_id=client_id
    )
    return {
        "access_token": token,
        "token_type": "bearer"
    }