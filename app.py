#!/usr/bin/python3
'''
Main Flask app which handles routing
'''

import os
from flask import Flask, request, jsonify, session, render_template, redirect, url_for, flash, make_response
from fastapi import Depends
from models.db_handler import DatabaseHandler
import requests
from auth import generate_pkce_pair, admin_required, check_current_user, verify_internal_secret, user_level
from dotenv import load_dotenv

load_dotenv(".env")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET")

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
)
app.config["SESSION_COOKIE_NAME"] = "client_session"


OAUTH_AUTHORIZE_URL = os.environ.get("OAUTH_AUTHORIZE_URL")
OAUTH_SERVER = os.environ.get("OAUTH_SERVER")
OAUTH_TOKEN_URL = os.environ.get("OAUTH_TOKEN_URL")
RESOURCE_API_BASE = os.environ.get("RESOURCE_API_BASE")
CLIENT_ID = os.environ.get("CLIENT_ID")
REDIRECT_URI = os.environ.get("REDIRECT_URI")
MAIN_APP_BASE = os.environ.get("MAIN_APP_BASE")


@app.route("/", methods=["GET"])
def landing_page():
    return render_template("landing_page.html")

@app.route("/register")
def register():
    auth_url = f"{OAUTH_SERVER}/register"
    return redirect(auth_url)

@app.route("/registration/complete", methods=["GET", "POST"])
def registration_completion():
    if request.method == "GET":
        return redirect(url_for("landing_page"))

    payload = request.get_json()

    if not payload:
        return jsonify({"error": "Missing JSON payload"}), 400
    verify_internal_secret(request)

    user_id = payload["user_id"]
    username = payload["username"]
    email = payload["email"]
    is_admin = payload["is_admin"]

    with DatabaseHandler() as db:
        db.store_users(user_id, username, email, is_admin)
    return {"status": "ok"}


@app.route("/login")
def login():
    verifier, challenge = generate_pkce_pair()
    session["pkce_verifier"] = verifier

    auth_url = (
        f"{OAUTH_AUTHORIZE_URL}?"
        f"response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    verifier = session.get("pkce_verifier")

    if not code or not verifier:
        flash("OAuth failed", "error")
        return redirect(url_for("landing_page"))


    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": verifier,
    }

    resp = requests.post(OAUTH_TOKEN_URL, data=data, cookies=request.cookies)

    if resp.status_code != 200:
        flash("Token exchange failed", "error")
        return redirect(url_for("landing_page"))

    token_json = resp.json()
    access_token = token_json.get("access_token")

    if not access_token:
        flash("No access token received", "error")
        return redirect(url_for("landing_page"))
    resp = make_response(redirect(url_for("dashboard")))

    resp.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=3600,
        path="/"
    )

    return resp


@app.route("/dashboard")
def dashboard():
    user = check_current_user(request)
    if not user:
        return redirect(url_for("login"))
    
    user_id = user["user_id"]

    resp = requests.get(
        f"{RESOURCE_API_BASE}/api/prescriptions/{user_id}",
        cookies=request.cookies,
    )
    prescriptions = resp.json() if resp.status_code == 200 else []


    if user.get("role") == "admin":
        return redirect(url_for("admin"))


    return render_template("dashboard.html", user=user, prescriptions=prescriptions)


@app.route("/admin")
def admin(admin=Depends(admin_required)):
    user = check_current_user(request)
    if not user or user.get("role") != "admin":
        return redirect(url_for("dashboard"))

    params = request.args
    resp = requests.get(
    f"{RESOURCE_API_BASE}/api/admin/prescriptions",
        params=params,
        cookies=request.cookies,
    )
    data = resp.json() if resp.status_code == 200 else []

    if data:
        prescriptions = data[0]
        aggregates = data[1]
    else:
        prescriptions = []
        aggregates = {}

    return render_template("admin.html", user=user, prescriptions=prescriptions, aggregates=aggregates)


@app.route("/upload", methods=["GET", "POST"])
def upload(user=Depends(user_level)):
    user = check_current_user(request)
    if not user:
        return redirect(url_for("login"))

    if user["role"] == "admin":
        return jsonify({"error": "Admin Can not Upload"}), 403
    user_id = user["user_id"]

    if request.method == "POST":
        files = {"file": request.files.get("file")}
        filename = files["file"].filename
        if not files or filename == "":
            return jsonify({"error": "Empty filename"}), 400

        try:
            with DatabaseHandler() as db:
                prescription_id = db.store_prescription(user_id, files)
        except Exception as e:
            return jsonify({"error": str(e)}), 500


        response = {
            "message": "Prescription uploaded",
            "prescription_id": prescription_id
        }

        if response:
            flash("Prescription uploaded successfully", "success")
        else:
            flash("Upload failed", "error")


    return render_template("upload.html", user=user)

@app.route("/prescriptions/upload", methods=["POST"])
def upload_prescription(user=Depends(user_level)):
    user = check_current_user(request)
    if not user:
        return redirect(url_for("login"))
    
    if user["role"] == "admin":
        return jsonify({"error": "Admin Can not Upload"}), 403
    user_id = user['user_id']

    file = request.files.get("file")

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    
    if not file or file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        with DatabaseHandler() as db:
            prescription_id = db.store_prescription(user_id, file)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


    return jsonify({
        "message": "Prescription uploaded",
        "prescription_id": prescription_id
    }), 201

@app.route("/logout")
def logout():
    session.clear()
    resp = redirect(url_for("landing_page"))
    resp.delete_cookie("access_token")
    resp.delete_cookie("session")
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)