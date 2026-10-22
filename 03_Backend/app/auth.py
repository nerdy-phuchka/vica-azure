import hmac
from dataclasses import dataclass
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings

bearer = HTTPBearer(auto_error=False)
_jwks = None
ROLES = {'RM','Analyst','Reviewer','Approver','Admin','LOS'}


@dataclass
class User:
    subject: str
    roles: set
    tenant: str


def identity(request: Request, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    global _jwks
    if not credentials:
        raise HTTPException(401, 'Bearer token required')
    s = settings()
    if s.dev_auth_enabled and s.app_mode == 'local':
        peer = request.client.host if request.client else ''
        proxy_secret=s.dev_proxy_secret
        trusted_proxy=bool(len(proxy_secret)>=24 and hmac.compare_digest(request.headers.get('X-VCA-Local-Proxy',''),proxy_secret))
        if peer not in ('127.0.0.1', '::1', 'testclient') and not trusted_proxy:
            raise HTTPException(403, 'Development identity is loopback-only')
        if not hmac.compare_digest(credentials.credentials, s.dev_auth_token):
            raise HTTPException(401, 'Invalid development token')
        subject = request.headers.get('X-Dev-User', 'demo-analyst')
        role = request.headers.get('X-Dev-Role', 'Analyst')
        if role not in ROLES:
            raise HTTPException(403, 'Unknown development role')
        return User(subject, {role}, 'local')
    try:
        issuer = f'https://login.microsoftonline.com/{s.entra_tenant_id}/v2.0'
        if _jwks is None:
            _jwks = jwt.PyJWKClient(f'https://login.microsoftonline.com/{s.entra_tenant_id}/discovery/v2.0/keys')
        signing = _jwks.get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(credentials.credentials, signing.key, algorithms=['RS256'],
                            audience=s.entra_audience, issuer=issuer,
                            options={'require':['exp','iat','iss','aud','tid']})
        if claims['tid'] != s.entra_tenant_id:
            raise ValueError('Tenant mismatch')
        roles = set(claims.get('roles', [])) & ROLES
        if not roles:
            raise HTTPException(403, 'No VCA role assigned')
        return User(claims.get('oid') or claims['sub'], roles, claims['tid'])
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, 'Invalid or expired identity token')


def require(user, *roles):
    if not user.roles.intersection(roles):
        raise HTTPException(403, 'Role does not permit this action')


def can_access(case, user):
    data = case.body()
    return data.get('tenant') == user.tenant and (user.subject in data.get('members', []) or 'Admin' in user.roles)
