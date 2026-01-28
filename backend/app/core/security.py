"""
Security utilities for JWT verification using Supabase JWKS (ES256/RS256).
"""
import base64
import json
import time
from typing import Any, Dict, List, Optional

import httpx
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from jose import JWTError, jwt

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger("security")

class JWKSClient:
    def __init__(self):
        # Configuration
        self.supabase_url = settings.SUPABASE_URL
        self.jwks_url: Optional[str] = None  # Will be discovered
        
        # Cache state
        self._cache: Dict[str, Any] = {}
        self._cache_time: float = 0
        self._cache_ttl: int = 3600
        
        # Fallback URLs if discovery fails
        self.fallback_urls = [
            f"{self.supabase_url}/auth/v1/jwks",
            f"{self.supabase_url}/.well-known/jwks.json",
            f"{self.supabase_url}/auth/v1/.well-known/jwks.json"
        ]

    async def get_key(self, kid: Optional[str] = None) -> str:
        """Fetch the key with matching kid"""
        jwks = await self.get_jwks()
        
        # Try to find key by kid
        if kid:
            key_data = next(
                (k for k in jwks.get("keys", []) if k.get("kid") == kid),
                None
            )
            
            if key_data:
                # logger.info(f"✅ Found key: {kid}")
                return self._jwk_to_pem(key_data)
        
        # Fallback: Use first key if kid not found or specified
        if jwks.get("keys"):
            logger.warning("Key ID not found or not provided, using first available key")
            return self._jwk_to_pem(jwks["keys"][0])
            
        raise AuthenticationError("No keys found in JWKS")

    async def get_jwks(self) -> Dict[str, Any]:
        """Get JWKS data with caching"""
        now = time.time()
        
        # Check cache
        if self._cache and (now - self._cache_time < self._cache_ttl):
            return self._cache
            
        # Refresh cache
        logger.info("Cache expired or empty, fetching fresh JWKS...")
        jwks = await self._fetch_jwks()
        
        self._cache = jwks
        self._cache_time = now
        return jwks
    
    async def _fetch_jwks(self) -> Dict[str, Any]:
        """Fetch JWKS using Discovery or Fallbacks"""
        
        # ATTEMPT 1: OIDC Discovery
        if not self.jwks_url:
            try:
                self.jwks_url = await self._discover_jwks_url()
            except Exception as e:
                logger.warning(f"OIDC Discovery failed: {e}")

        # ATTEMPT 2: If discovery worked (or was previously set to a working URL), fetch from it
        if self.jwks_url:
            jwks = await self._fetch_from_url(self.jwks_url)
            if jwks:
                logger.info("✅ OIDC Discovery/Cached URL successful")
                return jwks
        
        # ATTEMPT 3: Use hardcoded fallback paths
        for url in self.fallback_urls:
            # logger.info(f"Trying fallback: {url}")
            jwks = await self._fetch_from_url(url)
            if jwks:
                logger.info(f"✅ Fallback successful: {url}")
                # Update jwks_url so we use this working URL next time
                self.jwks_url = url 
                return jwks
        
        raise AuthenticationError("Failed to fetch JWKS from any source")

    async def _discover_jwks_url(self) -> Optional[str]:
        """Try to find JWKS URL via OIDC discovery"""
        oidc_url = f"{self.supabase_url}/auth/v1/.well-known/openid-configuration"
        async with httpx.AsyncClient() as client:
            response = await client.get(oidc_url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("jwks_uri")
        return None

    async def _fetch_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Helper to fetch JSON from a URL"""
        try:
            headers = {}
            if settings.SUPABASE_ANON_KEY:
                headers["apikey"] = settings.SUPABASE_ANON_KEY
                
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=5.0)
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass # Silently fail to allow other fallbacks to try
        return None

    @staticmethod
    def _jwk_to_pem(key_data: Dict[str, Any]) -> str:
        """Convert JWK to PEM format for PyJWT"""
        kty = key_data.get("kty")
        
        # Handle Elliptic Curve Keys (ES256)
        if kty == "EC":
            x_str = key_data.get("x")
            y_str = key_data.get("y")
            crv = key_data.get("crv", "P-256")
            
            def decode_b64(s: str) -> int:
                """Base64URL decode to integer"""
                padding = 4 - len(s) % 4
                if padding != 4:
                    s += "=" * padding
                return int.from_bytes(
                    base64.urlsafe_b64decode(s),
                    "big"
                )
            
            x = decode_b64(x_str)
            y = decode_b64(y_str)
            
            # Map curve name to cryptography object
            if crv == "P-256":
                curve = ec.SECP256R1()
            elif crv == "P-384":
                curve = ec.SECP384R1()
            elif crv == "P-521":
                curve = ec.SECP521R1()
            else:
                raise ValueError(f"Unsupported curve: {crv}")
            
            # Create public key object
            public_key = ec.EllipticCurvePublicNumbers(
                x, y, curve
            ).public_key(default_backend())
            
        # Handle RSA Keys (RS256)
        elif kty == "RSA":
            e = int.from_bytes(
                base64.urlsafe_b64decode(key_data['e'] + '=='),
                'big'
            )
            n = int.from_bytes(
                base64.urlsafe_b64decode(key_data['n'] + '=='),
                'big'
            )
            public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
            
        else:
            raise ValueError(f"Unsupported key type: {kty}")

        # Convert to PEM format
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return pem.decode()

# Global client instance
jwks_client = JWKSClient()

async def verify_supabase_token(token: str) -> dict:
    """
    Verify Supabase JWT token using correct key from JWKS.
    """
    try:
        # STEP 1: Extract the header (WITHOUT decoding)
        try:
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg", "HS256")
            kid = unverified_header.get("kid")
        except JWTError:
             raise AuthenticationError("Invalid token headers")
        
        # STEP 2: Handle HS256 (Shared Secret user/anon)
        if alg == 'HS256':
             return jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=['HS256'],
                audience="authenticated"
            )

        # STEP 3: Handle Asymmetric Keys (ES256, RS256, etc.)
        if alg in ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]:
            # Ensure we have the URL set
            if not settings.SUPABASE_URL:
                raise AuthenticationError("SUPABASE_URL is not configured")

            # Need to fetch public key from Supabase
            # MAGIC HAPPENS HERE
            public_key = await jwks_client.get_key(kid) 
            
            # STEP 4: Verify signature using the fetched key
            return jwt.decode(
                token,
                public_key,
                algorithms=[alg],
                audience="authenticated", 
                options={"verify_signature": True}
            )
            
        raise AuthenticationError(f"Unsupported algorithm: {alg}")
    
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
