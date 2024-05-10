import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi import BackgroundTasks
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from utils.custom_log import log
from models.user import UserLogin, UserCreate, UserReturn, LoginReturn, UserUpdate
from models.chat import ChatBody
from services.guard import check_token
from services.rag import save_file, add_url
from services.chat import connect_ai
from services.user import create_user, user_login, delete_user, get_user, update_user
from utils.db import get_db
from utils.invite_code import generate_invitation_code


@asynccontextmanager
async def lifespan(app: FastAPI):
    """ server 生命周期 """
    log.info("ai服务启动")
    yield
    log.info("ai服务关闭")

# 创建 FastAPI 实例
app = FastAPI(lifespan=lifespan)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    """ 根路径 """
    return {"Hello": "World"}


@app.post("/chat")
def chat(backgroundTasks: BackgroundTasks, body: ChatBody, user_id: int = Depends(check_token), ):
    """ 对话接口 """
    return connect_ai(body.query, user_id, backgroundTasks)


@app.post("/add_url", dependencies=[Depends(check_token)])
def rag_url(url: str):
    """ 添加网页链接，直接学习网页上的数据 """
    return add_url(url)


@app.post("/add_file", dependencies=[Depends(check_token)])
async def rag_file(pdf_file: UploadFile):
    """ 添加本地文件，直接学习本地文件中的数据 """
    log.info("开始保存文件: %s", pdf_file.filename)
    return await save_file(pdf_file)


@app.get("/invite_code")
def invite_code(role: str):
    """ 获取邀请码 """
    if role == os.getenv("INVITE_CODE_ROLE"):
        return {"invite_code": generate_invitation_code()}
    else:
        raise HTTPException(status_code=401, detail="没有操作权限")


@app.post("/register", response_model=UserReturn)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """ 用户注册 """
    return create_user(db, user)


@app.post("/login", response_model=LoginReturn)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """ 用户登录 """
    info = user_login(db, user)
    if not info:
        # 返回 401 错误
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的账号或密码",
        )
    # 返回登录信息
    return info


@app.delete("/user/delete")
def del_user(user_id: int = Depends(check_token), db: Session = Depends(get_db)):
    """ 删除用户 """
    return delete_user(db, user_id)


@app.get("/user/info")
def get_user_info(user_id: int = Depends(check_token), db: Session = Depends(get_db)):
    """ 获取用户信息 """
    return get_user(db, user_id)


@app.put("/user/update")
def update_user_info(user: UserUpdate, user_id: int = Depends(check_token), db: Session = Depends(get_db)):
    """ 更新用户信息 """
    return update_user(db, user_id, user)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """ WebSocket 服务 """
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
        except WebSocketDisconnect:
            break
