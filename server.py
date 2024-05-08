import os
import uuid

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import (BackgroundTasks, FastAPI, HTTPException, UploadFile,
                     WebSocket, WebSocketDisconnect)
from fastapi.staticfiles import StaticFiles
from langchain.document_loaders.pdf import PyPDFLoader
from langchain.globals import set_debug
from langchain_community.vectorstores.qdrant import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import (
    CharacterTextSplitter, HTMLHeaderTextSplitter)
from pydantic import BaseModel

from chat_agent import Master
from chat_consts import qdrant_path
from custom_log import log

# 加载环境变量配置文件
load_dotenv()


# 定义生命周期回调
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.debug("启动时执行的回调方法")
    yield
    log.debug("关闭时执行的回调方法")

app = FastAPI(lifespan=lifespan)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 设置调试模式
set_debug(False)


@app.get("/")
def read_root():
    return {"Hello": "World"}


class ChatBody(BaseModel):
    """ 对话请求体 """
    # 对话内容
    query: str
    # 用户ID，用于标识用户
    user_id: str = "user_id"


@app.post("/chat")
def chat(background_tasks: BackgroundTasks, body: ChatBody):
    """ 对话接口 """

    # 创建 Master
    master = Master(body.user_id)

    # 运行查询
    msg = master.run(body.query)

    # 生成唯一标识
    uid = str(uuid.uuid4())
    # 添加到后台任务
    background_tasks.add_task(
        master.background_voice_synthesis, msg["output"], uid)

    # 返回结果
    return {"msg": msg["output"], "id": uid}


@app.post("/add_url")
def add_url(url: str):
    """ 添加网页链接，直接学习网页上的数据 """
    # 文本分割
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
        ("h4", "Header 4"),
        ("p", "p"),
    ]
    html_splitter = HTMLHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on)

    documents = html_splitter.split_text_from_url(url)

    # 引入向量数据库
    qdrant = Qdrant.from_documents(
        documents=documents,
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        path=qdrant_path(),
        collection_name="local_documents"
    )
    log.info("向量数据库创建成功: %s", qdrant.client.get_collections())
    return {"ok": "添加成功"}


@app.post("/add_pdf")
async def add_pdf(pdf_file: UploadFile):
    """ 添加PDF文件，直接学习PDF文件中的数据 """

    # 检查文件类型是否为PDF
    if not pdf_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只允许上传PDF文件")

    # 存储PDF文件到临时文件
    temp_file_path = f"temp_{pdf_file.filename}"
    with open(temp_file_path, "wb") as out_file:
        out_file.write(await pdf_file.read())

    # 定义一个文本切割器
    text_splitter = CharacterTextSplitter(
        chunk_size=1000,  # 每个分割块的大小
        chunk_overlap=20,  # 分割块之间的重叠大小
        length_function=len,  # 用于计算文本长度的函数
        add_start_index=True,  # 是否在分割块中添加起始索引
    )

    # 加载并分割文档
    documents = PyPDFLoader(temp_file_path).load_and_split(text_splitter)

    log.info("分割结果: %s", documents)

    # 删除临时文件
    os.remove(temp_file_path)

    # 引入向量数据库
    Qdrant.from_documents(
        documents=documents,
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        path=qdrant_path(),
        collection_name="local_documents"
    )

    return {"ok": "添加成功"}


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
