
from fastapi import FastAPI,Depends, HTTPException
from jose import jwt
from fastapi import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

app=FastAPI()

# JWT Configuration

SECRET_KEY = "mysecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

#PASSWORD HASHING SETUP
pwd_context=CryptContext(schemes=["bcrypt"])

#OAUTH2 SETUP
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="login")



#Dummy user DB
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("1234")
    }
}

#Hash password function
def hash_password(password:str):
    return pwd_context.hash(password)

#Vrify password function
def verify_password(plain_password:str, hashed_password:str):
    return pwd_context.verify(plain_password, hashed_password)




#Create a function to create a JWT token
def create_token(data: dict):

    to_encode=data.copy()
    expire=datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    token=jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


# Login API (OAuth2PasswordRequestForm is used to get username and password from the request body)
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    token = create_token({"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}



#Token verification function

def verify_token(token: str=Depends(oauth2_scheme)):
    try:
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username=payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")



# Protected Route
@app.get("/secure")   # only for valid users 
def secure_data(user=Depends(verify_token)):
    return {"message":"This is a secure data", "user":user}