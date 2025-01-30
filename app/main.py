from fastapi import FastAPI,Response,status,HTTPException,Depends
from fastapi.params import Body
from pydantic import BaseModel          #we use pydantics to create a template of how a the data must be recieved
from typing import Optional
from random import randrange
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session
from . import models,schemas,utils
from .Database import engine, get_db
from .routers import post,users,auth


models.Base.metadata.create_all(bind = engine)

#CRUD operations
app = FastAPI()

while True:   
    try:
        conn = psycopg2.connect(host = 'localhost',database = 'fastapi',user = 'postgres',password = 'sudo',cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("Database connected successfully")
        break
        
    except Exception as error:
        print("Couldn't connect to database.. connection failed")
        print("error: ",error)
        time.sleep(2)

my_posts = [{"title":"Harleys in hawaii","content":"bikes in hawaii","rating":2,"id":3},{"title":"The legend of RF","content":"Rogers autoBG","rating":5,"id":8}]

@app.get("/")
def root():
    return {"message": "hello world"}

def find_post(id):
    for p in my_posts:
        if p["id"] == id:
            return p
        
app.include_router(post.router)
app.include_router(users.router)
app.include_router(auth.router)
        
@app.get("/sqlalchemy")
def test_posts(db: Session = Depends(get_db)):

    posts = db.query(models.Post).all()
    return posts


@app.get("/posts")              #we use .get only to fetch the post 
def get_posts(db: Session = Depends(get_db)):
    #getting posts using sql queries
    '''cursor.execute("""SELECT * FROM posts""")
    posts = cursor.fetchall()
    return posts'''

    #getting posts using alchemy 
    posts = db.query(models.Post).all()
    return posts
   
@app.post("/posts",status_code = status.HTTP_201_CREATED, response_model= schemas.Post)   #we use post to send some data and get the data after the modification from the server
def create_post(post:schemas.PostCreate,db: Session = Depends(get_db)):     #as in this case we are sending title and content and its returning us a post with the title n content printed 
    '''post_dict = post.dict()
    print(post_dict)
    post_dict["id"] = randrange(1,100000)
    my_posts.append(post_dict)'''

    #creating a post using sql queries
    '''cursor.execute("""INSERT INTO posts(title,content,published) VALUES (%s,%s,%s) RETURNING *""",(post.title,post.content,post.published))
    conn.commit()
    new_post = cursor.fetchone()
    return {"data": new_post}'''

    #creating a post using alchemy
    #new_post = models.Post(title = post.title,content = post.content,published = post.published)
    new_post = models.Post(**post.dict())       #always use this as its inefficient to pass each column 
    db.add(new_post)
    db.commit()
    db.refresh(new_post)        #displays the post that is created in postman 
    return new_post


@app.get("/posts/latest")
def latest_post():
    latestPost = my_posts[-1]
    return latestPost


@app.get("/posts/{id}")
def get_posts(id:int,response:Response,db: Session = Depends(get_db)):    
    #post = find_post(id)
    #getting posts by their id

    post = db.query(models.Post).filter(models.Post.id == id).first()

    if not post:                            
       raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail=f"post with id:{id} was not found")
       #the above method is the better way to display an error as compared to the below one
       
    '''response.status_code = status.HTTP_404_NOT_FOUND            #just have to type status. and a drop down box will appear and we can select the error to be shown
        return {"message":f"post with id {id} was not found"}'''
        
    return post


#lets try to delete a post which already exists
def find_index(id:int):
    i=0
    for p in my_posts:
        if p["id"] == id:
            index = i
            return(i)
        i += 1

    return -1

#however once the post is deleted its a good practice not to display anything after deletion hence the below code 
@app.delete("/posts/delete/{id}",status_code = status.HTTP_204_NO_CONTENT)
def delete_post(id:int ,db: Session = Depends(get_db)):
    '''index = find_index(id)
    my_posts.pop(index)
    return Response(status_code = status.HTTP_204_NO_CONTENT)'''

    #deleting a post using sql queries
    '''cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING*""",(str(id)))
    del_post = cursor.fetchone()
    conn.commit()'''

    #deleting a post using alchemy
    del_post = db.query(models.Post).filter(models.Post.id == id)

    if del_post.first() == None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail=f"post with id:{id} does not exist..")
    #return {"deleted post":del_post}

    del_post.delete(synchronize_session= False)
    db.commit()

    return Response(status_code = status.HTTP_204_NO_CONTENT)



#updating a post
@app.put("/posts/{id}")
def update_post(id:int,post:schemas.PostCreate,db: Session = Depends(get_db)):          # here the id is of the new post which is gonna replace the old post

    '''index = find_index(id)
    post_dict = post.dict()
    post_dict["id"] = id
    my_posts[index] = post_dict
    print(my_posts)'''


    #updating a post using sql queries
    '''cursor.execute("""UPDATE posts set content = %s WHERE id = %s RETURNING*""",(post.content,str(id)))
    upd_post = cursor.fetchone()
    conn.commit()'''

    #updating a post using alchemy
    post_query = db.query(models.Post).filter(models.Post.id == id)

    if post_query.first() == None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail=f"post with id:{id} does not exist..")

    #post_query.update({'title':'Rohit not a good captain','content':'getting out too quick'},synchronize_session=False)
    #we're hardcoding the values in the above a better way is below. here we have to pass in the values through postman

    post_query.update(post.dict(),synchronize_session=False)
    db.commit()

    return post_query.first()


@app.post("/users",status_code = status.HTTP_201_CREATED, response_model= schemas.UserOut)
def create_user(user:schemas.UserCreate,db: Session = Depends(get_db)):
    #hashing the password (basically not revealing the password in user.password) when it shows up in the db)
    hashed_password = utils.hash(user.password)         #importing from utils.py
    user.password = hashed_password

    new_user = models.User(**user.dict())       
    db.add(new_user)
    db.commit()
    db.refresh(new_user)       
    return new_user

@app.get("/users/{id}",response_model=schemas.UserOut)
def get_user(id:int,db:Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id:{id} does not exist")
    
    return user
