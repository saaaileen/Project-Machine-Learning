
import jwt
from datetime import timedelta

import bcrypt
from fastapi import FastAPI, Response, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer


from core.services.model_module import get_list_of_models
from core.dto.http_dto import HttpResponse, LoginRequest
from core.dto.token_dto import Token
from config.config_module import hashed_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, key, ALGORITHM

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login", auto_error=False)

def verify_token(request: Request):
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, key, algorithms=[ALGORITHM])
        password_in_token = payload.get("sub")
        if password_in_token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        if password_in_token != key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials in token")

        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

@app.get("/api/models/", dependencies=[Depends(verify_token)])
def read_root():
    list_of_models = get_list_of_models()

    return HttpResponse(
        code=200,
        status="success",
        messages="List of models retrieved successfully",
        data=list_of_models,
        error_message=None
    )

@app.post("/api/login")
def login(form_data: LoginRequest, response: Response):
    if bcrypt.checkpw(form_data.password.encode('utf-8'), hashed_password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.password}, expires_delta=access_token_expires
        )
        token = Token(access_token=access_token, token_type="bearer")
        response.set_cookie(key="access_token", value=token.access_token, httponly=True, samesite="lax")
        return HttpResponse(
            code=200,
            status="success",
            messages="Login successful",
            data=None,
            error_message=None
        )
    else:
        return HttpResponse(
            code=401,
            status="error",
            messages="Invalid credentials",
            data=None,
            error_message="Invalid credentials"
        )