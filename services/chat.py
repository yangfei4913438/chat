import uuid
from fastapi import BackgroundTasks
from agents.master import Master


def connect_ai(query: str, user_id: str, backgroundTasks: BackgroundTasks):
    """ 连接 AI 服务 """

    # 创建 Master
    master = Master(user_id)

    # 运行查询
    msg = master.run(query)

    # 生成唯一标识
    uid = str(uuid.uuid4())

    # 添加到后台任务
    backgroundTasks.add_task(
        master.background_voice_synthesis, msg["output"], uid)

    # 返回结果
    return {"msg": msg["output"], "id": uid}
