"""
Authentication and Authorization module for Smart Complaint System.
Implements token creation/validation (HMAC-SHA256 based signed tokens),
password hashing (NFR-02 adaptive hash), and RBAC access checks (NFR-03, FR-02).
"""

import json
import base64
import hmac
import hashlib
import time
import os
from typing import Optional, Dict, Any, List

SECRET_KEY = os.environ.get("SCS_SECRET_KEY", "scs_bandarlampung_smartcity_secret_key_2026!*")

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def base64url_decode(s: str) -> bytes:
    padding = '=' * (4 - (len(s) % 4)) if (len(s) % 4) != 0 else ''
    return base64.urlsafe_b64decode((s + padding).encode('utf-8'))

def create_access_token(user_id: str, email: str, full_name: str, roles: List[str], expires_in_seconds: int = 86400 * 7) -> str:
    """Generate signed JWT-like access token."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "name": full_name,
        "roles": roles,
        "iat": now,
        "exp": now + expires_in_seconds
    }
    
    header_b64 = base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        f"{header_b64}.{payload_b64}".encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = base64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify signed token and return payload if valid and not expired."""
    try:
        parts = token.strip().split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        expected_sig = hmac.new(
            SECRET_KEY.encode('utf-8'),
            f"{header_b64}.{payload_b64}".encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        if not hmac.compare_digest(base64url_decode(sig_b64), expected_sig):
            return None
            
        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        
        if payload.get("exp") and payload["exp"] < int(time.time()):
            return None # Expired
            
        return payload
    except Exception:
        return None

def check_permission(user_roles: List[str], required_roles: List[str]) -> bool:
    """Check if any of the user's roles match the required roles. Superadmin has full access."""
    if "SUPERADMIN" in user_roles:
        return True
    return any(role in required_roles for role in user_roles)

