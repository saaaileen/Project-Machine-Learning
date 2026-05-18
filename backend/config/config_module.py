from dotenv import load_dotenv
import os
import bcrypt
from datetime import datetime, timedelta, timezone
import jwt

load_dotenv()

key = os.getenv("SECRET_KEY")
token = os.getenv("SECRET_TOKEN")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES= int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
salt = bcrypt.gensalt()
hashed_password = bcrypt.hashpw(key.encode('utf-8'), salt)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, key, algorithm=ALGORITHM)
    return encoded_jwt