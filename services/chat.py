import os
import uuid
import asyncio
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Optional

from services.guard import check_token
from utils.custom_log import log
from agents.master import Master
from utils.oss import audio_exists


def connect_ai(query: str, user_id: str):
    """ 连接 AI 服务 """

    # 创建 Master
    master = Master(str(user_id))

    # 生成唯一标识
    uid = str(uuid.uuid4())

    # 运行查询
    result = master.run(query)

    log.info("返回数据: %s", result)

    data = result["output"]

    # 添加到后台任务
    asyncio.create_task(master.get_voice(data.replace("*", ""), uid))

    # 返回结果
    return {"msg": data, "id": uid}


# 存储client_id及其对应的WebSocket连接
connected_clients: Dict[str, WebSocket] = {}


async def connect_ws(websocket: WebSocket, token: str, role: Optional[str] = None, user_id: Optional[str] = None, tag_id: Optional[str] = None):
    """ 连接 WebSocket 服务 """

    # 模拟 http Bear Token
    http = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # 校验 token
    client_id = await check_token(http, role, user_id)

    # 如果不存在 client_id，则关闭连接
    if not client_id:
        log.error("用户 %s 连接失败", client_id)
        await websocket.close()
        return

    # 连接成功
    await websocket.accept()

    # 存储WebSocket连接
    connected_clients[client_id] = websocket
    log.info("用户 %s 已连接", client_id)

    try:
        while True:
            # 接收数据
            data = await websocket.receive_text()
            log.info("新收到的数据: %s", data)

            # 生成 连接 AI 服务的 key，用来识别用户
            key = f"{client_id}"
            if tag_id:
                key = f"{client_id}_{tag_id}"
            log.info("用户 %s 的 key: %s", client_id, key)

            # 连接 AI 服务
            result = connect_ai(data, key)
            data = {
                "id": result["id"],
                "message": result["msg"]
            }
            # 发送数据给客户端
            await websocket.send_json(data)
            # 异步执行，音频发送
            task = asyncio.create_task(check_audio(
                websocket, 'audio', result['id'], "mp3"))
            await task

    except WebSocketDisconnect:
        # 当客户端断开时，移除其连接
        del connected_clients[client_id]
        log.info("用户 %s 断开连接", client_id)


async def check_audio(websocket: WebSocket, target_dir: str, filename: str, file_extension: str = "mp3"):
    """ 检查音频是否存在并发送 """
    while True:
        # 检查音频是否存在
        if audio_exists(target_dir, f"{filename}.{file_extension}"):
            # 获取音频地址
            oss_url = os.getenv("OSS_ASSETS_URL")
            # 拼接完整地址
            full_url = f"{oss_url}/{target_dir}/{filename}.{file_extension}"
            # 判断 WebSocket 是否连接
            if websocket.client is not None:
                # 构建数据
                data = {
                    "id": filename,
                    "url": full_url
                }
                log.info("发送音频数据: %s", data)
                # 发送数据
                await websocket.send_json(data)
            else:
                log.error("客户端已断开连接")
                break
            break

        log.info("音频地址不存在，等待 1 秒钟...")
        await asyncio.sleep(1)  # 使用asyncio.sleep(1)来等待1秒
