"""
Security utilities for JWT verification using Supabase JWKS (RS256).
"""

import json
import os
from functools import lru_cache
from typing import Dict, Optional

import httpx
from jose import jwt, JWTError
from jose.backends.rsa_backend import RSAKey
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import base64

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger("security")

class JWKSClient:
    def __init__(self):
        self.jwks_url = f"{settings.SUPABASE_URL}/auth/v1/jwks"
        self.cache: Dict = {}
    
    async def get_key(self, kid: str = None) -> str:
        """Get public key from JWKS endpoint"""
        try:
            if not self.cache:
                async with httpx.AsyncClient() as client:
                    headers = {}
                    if settings.SUPABASE_ANON_KEY:
                        headers["apikey"] = settings.SUPABASE_ANON_KEY
                        
                    response = await client.get(self.jwks_url, headers=headers)
                    if response.status_code != 200:
                        # Log the response content for debugging
                        try:
                            error_body = response.text
                        except:
                            error_body = "No body"
                        logger.error(f"JWKS Fetch failed. Status: {response.status_code}, Body: {error_body}")
                        raise AuthenticationError(f"Failed to fetch JWKS from {self.jwks_url}")
                    self.cache = response.json()
            
            # If keys is empty, invalid config
            if 'keys' not in self.cache:
                 raise AuthenticationError("Invalid JWKS response format")

            # If kid not specified, use first key, otherwise find matching kid
            key_data = self.cache['keys'][0] if not kid else next(
                (k for k in self.cache['keys'] if k.get('kid') == kid),
                self.cache['keys'][0]
            )
            
            # Decode JWK components
            e = int.from_bytes(
                base64.urlsafe_b64decode(key_data['e'] + '=='),
                'big'
            )
            n = int.from_bytes(
                base64.urlsafe_b64decode(key_data['n'] + '=='),
                'big'
            )
            
            # Construct RSA public key
            public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
            
            # Export as PEM
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return pem.decode()
            
        except Exception as e:
            logger.error(f"JWKS Error: {str(e)}")
            raise AuthenticationError(f"Failed to load public key: {str(e)}")

# Global client instance
jwks_client = JWKSClient()

async def verify_supabase_token(token: str) -> dict:
    """
    Verify Supabase JWT token using RS256 and JWKS.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Decoded payload
    """
    try:
        # Get header to extract kid
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            alg = unverified_header.get('alg', 'RS256')
        except JWTError:
            raise AuthenticationError("Invalid token headers")
            
        # If the token is explicitly HS256 (e.g. anon key), try standard secret verification
        # This handles the case where anon token is sent or mixed environments
        if alg == 'HS256':
             return jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=['HS256'],
                audience="authenticated"
            )

        # Ensure we have the URL set
        if not settings.SUPABASE_URL:
            raise AuthenticationError("SUPABASE_URL is not configured")

        # Get public key
        public_key = await jwks_client.get_key(kid)
        
        # Verify and decode
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            # Check audience if configured, otherwise relax check for development
            audience="authenticated", 
            options={"verify_signature": True}
        )
        
        return payload
    
    except JWTError as e:
        logger.warning(f"JWT Verification failed: {str(e)}")
        raise AuthenticationError(f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected verification error: {str(e)}")
        raise AuthenticationError(f"Token verification failed: {str(e)}")


def extract_user_from_token(payload: dict) -> dict:
    """
    Extract user information from decoded JWT payload.

    Args:
        payload: Decoded JWT token payload

    Returns:
        dict: User information including id, email, and metadata
    """
    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated"),
        "app_metadata": payload.get("app_metadata", {}),
        "user_metadata": payload.get("user_metadata", {}),
    }
