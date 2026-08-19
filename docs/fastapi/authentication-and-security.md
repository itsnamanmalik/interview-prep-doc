---
icon: material/shield-key-outline
---

# Authentication & Security

FastAPI gives you security *primitives* that integrate with OpenAPI, not a user system. Django hands you users, groups, permissions and sessions; here you build the backend and own the decisions.

### The building blocks

```python
from fastapi.security import (
    OAuth2PasswordBearer,        # reads "Authorization: Bearer <token>"
    OAuth2PasswordRequestForm,   # parses the username/password form body
    HTTPBearer,
    HTTPBasic,
    APIKeyHeader,
)
```

Each is a dependency *and* a schema contributor: declaring one makes `/docs` grow a working **Authorize** button, which is a genuinely useful answer to "why not just read the header yourself?".

### JWT authentication end to end

!!! note "Dependencies"
    `pip install pyjwt "pwdlib[argon2]" python-multipart`. The `python-multipart`
    part is easy to miss — `OAuth2PasswordRequestForm` reads a form body, and
    without it FastAPI raises `RuntimeError: Form data requires "python-multipart"
    to be installed` at import time. `pip install "fastapi[standard]"` bundles it.

```python
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt                                   # pip install pyjwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash               # pip install "pwdlib[argon2]"

SECRET_KEY = "load-me-from-the-environment"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

password_hash = PasswordHash.recommended()    # Argon2id
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()

fake_users = {
    "alice": {"username": "alice", "hashed_password": password_hash.hash("secret")}
}

def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": subject, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token")
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = fake_users.get(form.username)
    if not user or not password_hash.verify(form.password, user["hashed_password"]):
        # Deliberately vague: do not reveal whether the username exists.
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return {"access_token": create_access_token(form.username), "token_type": "bearer"}

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise credentials_error
    username = payload.get("sub")
    if username is None or username not in fake_users:
        raise credentials_error
    return {"username": username}

@app.get("/users/me")
async def me(user: Annotated[dict, Depends(get_current_user)]):
    return user
```

Points that earn credit:

- **`algorithms=[ALGORITHM]` on decode is mandatory.** Accepting whatever the token's header claims allows the `alg: none` attack, and letting an attacker downgrade RS256 to HS256 lets them sign with the public key.

- **`exp` is verified by `jwt.decode` automatically.** Do not hand-roll expiry checking.

- **Hash with Argon2 or bcrypt, never SHA-256.** Fast hashes are the wrong tool for passwords.

!!! warning "`passlib` is no longer a safe default"
    Most FastAPI tutorials still show `passlib[bcrypt]`. Passlib's last release was
    2020 and it reads `bcrypt.__about__.__version__`, which **bcrypt 4.1 removed**.
    On a current install its version detection fails and hashing then dies with
    `ValueError: password cannot be longer than 72 bytes` — even for a six-character
    password. Use [`pwdlib`](https://frankie567.github.io/pwdlib/), which is what
    FastAPI's own docs moved to, or call `bcrypt` directly.

- **Return one vague error for bad user and bad password.** Distinguishing them is a user-enumeration oracle.

### Scopes for finer-grained authorisation

```python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import SecurityScopes

app = FastAPI()

def current_token_scopes() -> list[str]:
    return ["items:read"]            # in reality, from the decoded JWT

def require_scopes(
    security_scopes: SecurityScopes,
    granted: Annotated[list[str], Depends(current_token_scopes)],
) -> None:
    for scope in security_scopes.scopes:
        if scope not in granted:
            raise HTTPException(
                status_code=403,
                detail=f"Missing scope: {scope}",
                headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
            )

@app.get("/items", dependencies=[Security(require_scopes, scopes=["items:read"])])
async def read_items():
    return ["ok"]

@app.delete("/items/{item_id}", dependencies=[Security(require_scopes, scopes=["items:write"])])
async def delete_item(item_id: int):
    return {"deleted": item_id}
```

`Security` is `Depends` plus a `scopes` argument; `SecurityScopes` lets one dependency read what the endpoint asked for, so you write the check once.

### Access and refresh tokens

Short-lived access token, long-lived refresh token, and a reason for each:

- **Access token** (5–15 min): sent on every request, not revocable — so keep the window small.

- **Refresh token** (days–weeks): used only against `/refresh`, stored server-side or as a rotating family so it *can* be revoked.

The senior point is that **stateless JWTs cannot be revoked**. Logout, ban and password-change therefore need either a short expiry you are willing to tolerate, or a denylist of `jti` values in Redis — at which point you have reintroduced state, and should say so rather than pretend JWTs are free.

### Hardening checklist

- **Secrets from the environment**, never in source. `pydantic-settings` makes them typed and required at boot.

- **CORS narrowly.** `allow_origins=["*"]` with `allow_credentials=True` is rejected by browsers and is a smell in review.

- **Rate limit** login and token endpoints — `slowapi`, or at the gateway.

- **Validate at the edge.** Pydantic constraints (`max_length`, `ge`, `le`) are your first line against oversized payloads.

- **Never log tokens or passwords.** Redact in exception handlers too.

- **Turn off `/docs` in production**, or put it behind auth: it is a complete map of your API.

- **Use parameterised queries.** The ORM does this; hand-written `text()` with f-strings does not.

- **`HTTPException` details are user-visible.** Do not leak stack traces or SQL.

- **HTTPS and `Strict-Transport-Security`**, terminated at the proxy.

### Trusted hosts and HTTPS redirect

```python
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com"])
```

This is the FastAPI equivalent of Django's `ALLOWED_HOSTS`, and it is not on by default — a difference worth flagging, since Django trains you to expect it.

### Cookies vs bearer tokens

| | Bearer token in header | Session cookie |
| --- | --- | --- |
| CSRF risk | None (not sent automatically) | Real — needs CSRF protection |
| XSS risk | High if kept in `localStorage` | Lower with `HttpOnly` |
| Mobile / service clients | Natural fit | Awkward |
| Revocation | Hard when stateless | Easy, delete server-side |

For a browser SPA, `HttpOnly` + `Secure` + `SameSite=Lax` cookies plus CSRF protection is often the safer default. Bearer tokens suit service-to-service and mobile clients. Saying "it depends on the client" is the correct answer.
