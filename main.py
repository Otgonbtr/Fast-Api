from fastapi import FastAPI, status , Depends, HTTPException
import models
from database import engine,SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
import uvicorn
import auth

app = FastAPI()
app.include_router(auth.router)
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get('/',status_code=status.HTTP_200_OK)
async def user(user: None, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return {"user": user}


if __name__ == "__main__":
    uvicorn.run(app, host="192.168.6.155", port=8087)