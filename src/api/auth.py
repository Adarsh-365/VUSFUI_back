# auth.py

import os
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

authrouter = APIRouter(prefix="/auth", tags=["Auth"])

ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
JWT_SECRET = os.getenv("JWT_SECRET")

ALGORITHM = "HS256"

security = HTTPBearer()


class LoginRequest(BaseModel):
    user_id: str
    password: str


@authrouter.post("/login")
def login(data: LoginRequest):
    print(  data.user_id , ADMIN_USER_ID
            , data.password , ADMIN_PASSWORD)

    if (
        data.user_id != ADMIN_USER_ID
        or data.password != ADMIN_PASSWORD
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid user ID or password"
        )

    expire = datetime.now(timezone.utc) + timedelta(hours=8)

    token = jwt.encode(
        {
            "sub": ADMIN_USER_ID,
            "exp": expire,
        },
        JWT_SECRET,
        algorithm=ALGORITHM
    )

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer"
    }


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id != ADMIN_USER_ID:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized"
            )

        return user_id

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )