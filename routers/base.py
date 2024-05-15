from typing import Optional
from fastapi import UploadFile, WebSocket, Depends, APIRouter
from utils.custom_log import log
from models.chat import ChatBody
from services.guard import check_token
from services.rag import save_file, add_url
from services.chat import connect_ai, connect_ws


router = APIRouter()


@router.get("/")
def read_root():
    """ 根路径 """
    return {"Hello": "World"}


@router.post("/chat")
async def chat(body: ChatBody, user_id: int = Depends(check_token), ):
    """ 对话接口 """
    return connect_ai(body.query, user_id)


@router.post("/add_url", dependencies=[Depends(check_token)])
def rag_url(url: str):
    """ 添加网页链接，直接学习网页上的数据 """
    return add_url(url)


@router.post("/add_file", dependencies=[Depends(check_token)])
async def rag_file(pdf_file: UploadFile):
    """ 添加本地文件，直接学习本地文件中的数据 """
    log.info("开始保存文件: %s", pdf_file.filename)
    return await save_file(pdf_file)


@router.websocket("/ws/{token}/{role:str}/{user_id:str}")
async def websocket_endpoint_role(websocket: WebSocket, token: str, role: Optional[str] = None, user_id: Optional[str] = None):
    """ WebSocket 服务, 有特权"""
    await connect_ws(websocket, token, role, user_id, None)


@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """ WebSocket 服务, 无特权 """
    await connect_ws(websocket, token, None, None, None)


@router.websocket("/ws/{token}/{tag_id}")
async def websocket_endpoint_tag(websocket: WebSocket, token: str, tag_id: str):
    """ WebSocket 服务, 无特权 """
    await connect_ws(websocket, token, None, None, tag_id)
