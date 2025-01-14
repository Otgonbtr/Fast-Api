from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from models import Users
from jose import JWTError, jwt
from database import SessionLocal
from passlib.context import CryptContext
from starlette import status
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

SECRET_KEY  = 'vd54fv5df4vd8gh65ng5h5er5g6hjm658df23erg1e3rg'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
# class CreateUserRequest(BaseModel):
#     username: str
#     password: str
# @router.post('/', status_code=status.HTTP_201_CREATED)
# async def create_user(create_user_request: CreateUserRequest, db: db_dependency):
#     create_user_model = Users(username=create_user_request.username, hashed_password=bcrypt_context.hash(create_user_request.password), score=0)
#     db.add(create_user_model)
#     db.commit()

##------------------------------- Create user -----------------------------------##
@router.put('/', status_code=status.HTTP_201_CREATED)
async def create_user(username: str,password: str, db: db_dependency):
    create_user_model = Users(username=username, hashed_password=bcrypt_context.hash(password), score=0)
    db.add(create_user_model)
    db.commit()

##---------------------------------- Login ---------------------------------------##
@router.post('/token', response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    db = SessionLocal()
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(user.username,user.id,timedelta(minutes=20))
    db.close()
    return {"access_token": token, "token_type": "bearer"}
    
##---------------------------- Authenticate user ----------------------------------##
def authenticate_user(db, username: str, password: str):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        db.close()
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        db.close()
        return False
    return user

##----------------------------- Create access token --------------------------------##
def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


##----------------------------------- Change score ---------------------------------##
db_dependency2 = SessionLocal()
def get_user(username: str):
    user = db_dependency2.query(Users).filter(Users.username == username).first()
    if user:
        return user
    return None

async def get_current_user(token: str = Depends(oauth2_bearer)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    user = get_user(username=username)
    if user is None:
        raise credentials_exception
    return user

@router.put("/users/me/score")
async def update_user_score(score: int, current_user: Users = Depends(get_current_user), token: str = Depends(oauth2_bearer)):
    beforescore = current_user.score
    current_user.score = score
    db_dependency2.commit()
    db_dependency2.refresh(current_user)
    return current_user, {"message": "Score updated successfully"}, {"Before score": beforescore}, {"Access token": token}


##------------------------------ Update user password --------------------------------##
@router.put('/{user_id}',status_code=status.HTTP_200_OK)
async def update_user_password(password: str, db: db_dependency, user: Users = Depends(get_current_user)):
    user = db.query(Users).filter(Users.id == user.id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.username = user.username
    user.hashed_password = bcrypt_context.hash(password)
    # db.commit()
    return {"user": user}