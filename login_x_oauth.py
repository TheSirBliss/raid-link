from flask import Flask, redirect, request
import requests
import json
import os
import base64
import hashlib
import secrets
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = "supersegretodigitale"

CLIENT_ID = "77anZvMmYRLFfTjCo2beKuYta"
CLIENT_SECRET = "peLjGGLL54cczAYnVxHJ3RE78NVeyf0VDRlQ1f0fIyQbzZm7yD"
REDIRECT_URI = "https://raid-link.onrender.com/callback"
SCOPES = "tweet.read users.read like.read offline.access"

# PKCE utils
def generate_pkce_pair():
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode('utf-8')
    return code_verifier, code_challenge

# In memoria solo per demo
code_verifier_global = ""

@app.route("/")
def index():
    global code_verifier_global
    code_verifier, code_challenge = generate_pkce_pair()
    code_verifier_global = code_verifier

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": "securestate",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    auth_url = "https://twitter.com/i/oauth2/authorize?" + urlencode(params)
    return f"<h2>Collega il tuo profilo X</h2><a href='{auth_url}'>Autorizza via Twitter</a>"

@app.route("/callback")
def callback():
    global code_verifier_global
    code = request.args.get("code")
    if not code:
        return "Errore: nessun codice ricevuto."

    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier_global
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    r = requests.post("https://api.twitter.com/2/oauth2/token", data=data, headers=headers, auth=(CLIENT_ID, CLIENT_SECRET))
    if r.status_code != 200:
        return "Errore durante lo scambio token: " + r.text

    token_data = r.json()
    access_token = token_data.get("access_token")

    user_info = requests.get(
        "https://api.twitter.com/2/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    user_id = user_info.get("data", {}).get("id")
    username = user_info.get("data", {}).get("username")

    record = {
        "twitter_id": user_id,
        "username": username,
        "access_token": access_token
    }

    if os.path.exists("linked_users.json"):
        with open("linked_users.json", "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[user_id] = record
    with open("linked_users.json", "w") as f:
        json.dump(data, f, indent=4)

    return f"<h3>Collegamento completato!</h3><p>Benvenuto, @{username}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
