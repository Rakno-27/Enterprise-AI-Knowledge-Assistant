import jwt
import httpx
import time
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.core.config import settings

class JWKSCache:
    _keys: Dict[str, Any] = {}
    _last_fetched: float = 0.0

    @classmethod
    async def get_keys(cls) -> Dict[str, Any]:
        # Cache public keys for 1 hour to prevent flooding Auth0 endpoints
        if not cls._keys or (time.time() - cls._last_fetched) > 3600:
            try:
                url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    cls._keys = response.json()
                    cls._last_fetched = time.time()
            except Exception as e:
                print(f"[Auth] Failed to fetch JWKS keys from Auth0: {e}")
        return cls._keys

class UserClaims(BaseModel):
    sub: str
    email: Optional[str] = None
    roles: List[str] = []
    permissions: List[str] = []

security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(token: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> UserClaims:
    # 1. Local Bypass Mode (For local development/testing)
    if settings.BYPASS_AUTH:
        if not token:
            # Return default user if no authorization header present and bypass is active
            return UserClaims(
                sub="mock|user",
                email="user@enterprise.com",
                roles=["user"],
                permissions=[]
            )
        
        cred = token.credentials.strip()
        if cred == "mock_admin":
            return UserClaims(
                sub="mock|admin",
                email="admin@enterprise.com",
                roles=["admin", "user"],
                permissions=["admin:documents"]
            )
        elif cred in ["mock_user", "mock_token", "true", ""]:
            return UserClaims(
                sub="mock|user",
                email="user@enterprise.com",
                roles=["user"],
                permissions=[]
            )
        # If any other credential is provided, fall through to try real verification

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )

    token_str = token.credentials

    # 2. Real Auth0 Verification
    if settings.AUTH0_DOMAIN:
        try:
            jwks = await JWKSCache.get_keys()
            unverified_header = jwt.get_unverified_header(token_str)
            
            rsa_key = {}
            for key in jwks.get("keys", []):
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break
            
            if not rsa_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token header: signing key not found"
                )

            from jwt.algorithms import RSAAlgorithm
            public_key = RSAAlgorithm.from_jwk(rsa_key)

            payload = jwt.decode(
                token_str,
                public_key,
                algorithms=settings.AUTH0_ALGORITHMS,
                audience=settings.AUTH0_AUDIENCE,
                issuer=f"https://{settings.AUTH0_DOMAIN}/"
            )

            # Extract custom claims and default scopes
            roles = payload.get("https://enterprise-assistant.com/roles", [])
            if not roles:
                roles = payload.get("roles", [])
            permissions = payload.get("permissions", [])

            # Map permissions to roles for developer convenience
            if "admin:documents" in permissions and "admin" not in roles:
                roles.append("admin")
            if not roles:
                roles = ["user"]

            return UserClaims(
                sub=payload.get("sub", ""),
                email=payload.get("email"),
                roles=roles,
                permissions=permissions
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {e}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication domain is not configured and local bypass is disabled"
        )

class RequireRole:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: UserClaims = Depends(get_current_user)) -> UserClaims:
        # Admin gets bypass access to all operations
        if "admin" in user.roles:
            return user
            
        for role in self.allowed_roles:
            if role in user.roles:
                return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access forbidden: requires one of the following roles: {', '.join(self.allowed_roles)}"
        )
