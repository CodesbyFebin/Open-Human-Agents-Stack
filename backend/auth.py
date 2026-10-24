"""Simple bearer API-key authentication and tenant isolation."""
import os
import hashlib
from fastapi import Depends, HTTPException, Header
from typing import Optional
from .db import fetch_one

def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")
    user = fetch_one(
        "SELECT id, org_id, email, role FROM users WHERE api_key_hash = %s",
        (hash_key(token),)
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user

def require_role(required: str):
    async def checker(user=Depends(get_current_user)):
        if user["role"] not in (required, "admin"):
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return checker
