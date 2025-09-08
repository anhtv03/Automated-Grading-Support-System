import re
import secrets
import string

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["sha512_crypt"], deprecated="auto")


@staticmethod
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


@staticmethod
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


@staticmethod
def is_valid_password(password: str) -> bool:
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,50}$'
    return bool(re.match(pattern, password))


@staticmethod
def generate_random_password(length: int = 8) -> str:
    if not 8 <= length <= 50:
        raise ValueError("Length must be between 8 and 50 characters")

    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = string.punctuation
    all_chars = lowercase + uppercase + digits + special

    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]

    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))

    secrets.SystemRandom().shuffle(password)
    return ''.join(password)
