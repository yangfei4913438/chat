from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from utils.custom_log import log
from routers.base import router as base_router
from routers.user import router as user_router
from routers.tag import router as tag_router
from routers.message import router as message_router


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

# 加载路由
app.include_router(base_router, tags=["基础接口"])
app.include_router(user_router, tags=["用户接口"])
app.include_router(tag_router,  tags=["会话标签接口"])
app.include_router(message_router, tags=["消息接口"])
