"""
API Key authentication

Features to implement:
- API key validation dependency
- Security headers
- API key from header: X-API-Key
"""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import settings


# TODO: Implement API key authentication here

