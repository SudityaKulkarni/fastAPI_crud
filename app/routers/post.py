from fastapi import FastAPI,Response,status,HTTPException,Depends,APIRouter
from typing import List
from .. import models,schemas,oauth2
from sqlalchemy.orm import Session
from ..Database import get_db


router = APIRouter(prefix="/posts",tags=['posts'])

@router.get("/")
def root():
    return {"message": "hello world"}


@router.get("/sqlalchemy")
def test_posts(db: Session = Depends(get_db)):

    posts = db.query(models.Post).all()
    return posts


@router.get("/",response_model= List[schemas.Post])              #we use .get only to fetch the post 
def get_posts(db: Session = Depends(get_db),current_user:int = Depends(oauth2.get_current_user)):
    
    posts = db.query(models.Post).all()
    return posts
   
@router.post("/",status_code = status.HTTP_201_CREATED, response_model= schemas.Post)   #we use post to send some data and get the data after the modification from the server
def create_post(post:schemas.PostCreate,db: Session = Depends(get_db) ,current_user:int = Depends(oauth2.get_current_user)):  #as in this case we are sending title and content and its returning us a post with the title n content printed 
    
    #creating a post using alchemy
    #new_post = models.Post(title = post.title,content = post.content,published = post.published)
    print(current_user)
    new_post = models.Post(**post.dict())       #always use this as its inefficient to pass each column 
    db.add(new_post)
    db.commit()
    db.refresh(new_post)        #displays the post that is created in postman 
    return new_post

@router.get("/{id}")
def get_posts(id:int,response:Response,db: Session = Depends(get_db),current_user:int = Depends(oauth2.get_current_user)):    
    post = db.query(models.Post).filter(models.Post.id == id).first()

    if not post:                            
       raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail=f"post with id:{id} was not found")

    return post

#however once the post is deleted its a good practice not to display anything after deletion hence the below code 
@router.delete("/delete/{id}",status_code = status.HTTP_204_NO_CONTENT)
def delete_post(id:int ,db: Session = Depends(get_db),current_user:int = Depends(oauth2.get_current_user)):

    del_post = db.query(models.Post).filter(models.Post.id == id)

    if del_post.first() == None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail=f"post with id:{id} does not exist..")
    #return {"deleted post":del_post}

    del_post.delete(synchronize_session= False)
    db.commit()

    return Response(status_code = status.HTTP_204_NO_CONTENT)



#updating a post
@router.put("/{id}")
def update_post(id:int,post:schemas.PostCreate,db: Session = Depends(get_db),current_user:int = Depends(oauth2.get_current_user)):          # here the id is of the new post which is gonna replace the old post

    post_query = db.query(models.Post).filter(models.Post.id == id)

    if post_query.first() == None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail=f"post with id:{id} does not exist..")

    #post_query.update({'title':'Rohit not a good captain','content':'getting out too quick'},synchronize_session=False)
    #we're hardcoding the values in the above a better way is below. here we have to pass in the values through postman

    post_query.update(post.dict(),synchronize_session=False)
    db.commit()

    return post_query.first() 
