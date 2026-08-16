import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

SECRET_KEY = "CHANGE_ME_use_a_64_char_random_secret"   # from settings on Day 6
ALGORITHM = "HS256"
ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=7)


def hash_password(raw: str) -> str:
    # bcrypt operates on the first 72 bytes; truncate explicitly so long
    # passwords don't raise on bcrypt >= 4.1.
    pw = raw.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")

def verify_password(raw: str, hashed: str) -> bool:
    pw = raw.encode("utf-8")[:72]
    return bcrypt.checkpw(pw, hashed.encode("utf-8"))


def _create_token(sub: str, ttl: timedelta, token_type: str, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,                       # subject = user id
        "type": token_type,               # "access" | "refresh"
        "iat": now,
        "exp": now + ttl,
        **(extra or {}),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(sub: str, role: str) -> str:
    return _create_token(sub, ACCESS_TTL, "access", {"role": role})

def create_refresh_token(sub: str) -> str:
    return _create_token(sub, REFRESH_TTL, "refresh")

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise ValueError("invalid token")