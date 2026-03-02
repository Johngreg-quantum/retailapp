from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status

SECRET_KEY = "SUPER_SECRET_LACOSTE_KEY" # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200 # 30 Days for retail convenience

def create_magic_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=15) # Link expires fast
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401)
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Link expired or invalid")