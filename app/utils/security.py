import random
import string
from datetime import timedelta, datetime, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["sha512_crypt"], deprecated="auto")

SECRET_KEY = "sep490auto10ddcm"
ALGORITHM = "HS512"
ACCESS_TOKEN_EXPIRE_MINUTES = 1


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # create jwt access token
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


@staticmethod
def generate_otp(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))
