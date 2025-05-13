from fastapi import FastAPI, Depends, HTTPException , Form , APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal , engine , Base
from jose import jwt , JWTError
from utils import hash_password , verify_password
from pydantic import BaseModel
from database import get_db
from schemas import PostUpdate , UserUpdate , createPost
import models , schemas , posts
from utils import verify_token , create_token
from datetime import datetime , timedelta

app = FastAPI() # 서버 생성 

models.Base.metadata.create_all(bind=engine) # 실제로 orm용 테이블 만들기
app.include_router(posts.router)

@app.get("/protected") # 로그인 세션 확인
def protected_route(user : models.User = Depends(verify_token) , db : Session = Depends(get_db)):
    return {
        "id" : user.id , 
        "username" : user.username ,
        "message" : "토큰 사용자만 접근가능"
    }
    
    
@app.post("/signup") # 회원가입
def signup(username : str , password : str , db : Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first() 
    if user : 
        raise HTTPException(status_code = 409 , detail = "중복되는 ID입니다.")
    
    hashed_pw = hash_password(password)
    new_users = models.User(username = username , password = hashed_pw)
    db.add(new_users)
    db.commit()
    db.refresh(new_users)
    return {"message":f'{username}님 회원가입이 완료되었습니다!'}

@app.post("/login") # 로그인 
def login(
    username: str = Form("name"),
    password: str = Form("password"),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 ID입니다.")

    if not verify_password(password , user.password) :
        raise HTTPException(status_code=401, detail="비밀번호가 틀렸습니다.")

    access_token_expires = timedelta(minutes=30)
    access_token = create_token(
        data={"sub": user.username},
        expires_time=access_token_expires
    )

    return {
        "access_token": access_token,   
        "token_type": "bearer"          
    }
    
@app.put("/user") # 회원정보 수정,변경 
def update_user(update : UserUpdate, user : models.User = Depends(verify_token), db : Session = Depends(get_db)):
    user.username = update.username
    user.password = hash_password(update.password)
    db.commit()
    return {"message" : "회원정보가 수정되었습니다."}

@app.delete("/user") # 회원 정보 삭제 
def delete_user(user : models.User = Depends(verify_token) , db : Session = Depends(get_db)):
    db.delete(user)
    db.commit()
    return {"message" : f'{user.username}님, 탈퇴가 완료되었습니다.'}

@app.post("/Post" , response_model = schemas.PostOut) # 게시글 쓰기 
def Post(post : createPost , user : models.User = Depends(verify_token), db : Session = Depends(get_db)):
    new_post = models.Post(title = post.title , content = post.content , owner_id = user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post
