from fastapi import APIRouter,FastAPI,Response,status,HTTPException,Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..Database import get_db
from .. import schemas,models,utils,oauth2


router = APIRouter(tags = ['Authentication'])

@router.post("/login",response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends() ,db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"Invalid credentials")
    
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"Invalid credentials")
    
    access_token = oauth2.create_access_token({"user_id": user.id})
    #return token
    return{"access_token": access_token,"token_type":"bearer"}






