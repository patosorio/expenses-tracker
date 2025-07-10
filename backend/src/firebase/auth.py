from pathlib import Path

import firebase_admin
from firebase_admin import credentials, auth

from src.config import settings

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    firebase_creds = Path(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
    cred = credentials.Certificate(str(firebase_creds))
    firebase_admin.initialize_app(cred)

async def verify_firebase_token(token: str) -> dict:
    """Verify Firebase ID token and return user info"""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")
    
