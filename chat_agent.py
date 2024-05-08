import asyncio
import os

import requests
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationTokenBufferMemory
from langchain_community.chat_message_histories.redis import \
    RedisChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from chat_template import moods, sys_template
from chat_tools import bazi_cesuan, jiemeng, local_db, search, shengxiao, yaogua, jiuxing, bazi_hehun, weilai, chenggu, zeshi, qiming
from utils.oss import upload

from custom_log import log

# 创建工具集
tools = [
    local_db, bazi_cesuan, jiemeng, yaogua, shengxiao, jiuxing, bazi_hehun, weilai, chenggu, zeshi, qiming, search
]


class Master:
    def __init__(self, user_id: str = "user_id"):
        # 创建 chat model
        self.chatModel = ChatOpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_API_BASE'),
            streaming=True,  # 支持流式处理, 支持 websocket
            temperature=0,  # 不让模型生成随机性
        )
        self.QingXu = "default"
        # 创建内存 key
        self.memory_key = "chat_history"
        # 创建内存
        self.memory = self.get_memory(user_id)
        memory = ConversationTokenBufferMemory(
            llm=self.chatModel,  # 语言模型
            human_prefix="用户",  # 人类的前缀
            ai_prefix="周大师",  # AI 的前缀
            memory_key=self.memory_key,  # 内存 key
            output_key="output",  # 输出 key
            max_token_limit=1000,  # 最大 token 限制，避免内存使用无限增长
            return_messages=True,  # 返回消息
            chat_memory=self.memory,  # 聊天内存
        )

        # 创建 prompt, 用于格式化输入输出
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                sys_template.format(who_you_are=moods[self.QingXu]["roleSet"])
            ),
            # 内存占位符
            MessagesPlaceholder(variable_name=self.memory_key),
            (
                "user",
                "{input}"
            ),
            # 消息占位符，这里必须要有，用于格式化输出
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # 创建 agent
        agent = create_openai_tools_agent(
            llm=self.chatModel,
            prompt=self.prompt,
            tools=tools,
        )

        # 创建 agent 执行器
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            # return_intermediate_steps=True, # 开启中间步骤返回，只有在需要调试的时候开启，或者需要返回中间步骤的时候开启
        )

    def run(self, query):
        log.info("执行用户输入: %s", query)

        # 提取用户的情绪类型
        self.qingxu_chain(query)

        # 执行 agent
        result = self.agent_executor.invoke(
            {"input": query},
            return_only_outputs=True  # 只返回output输出
        )

        # data = result["intermediate_steps"][0]
        # action = data[0]
        # tool_name = action.tool

        # if tool_name == "bazi_cesuan":
        #     prompt = ChatPromptTemplate.from_template(
        #         "{sys_template} \n结合你自身的专业，对下面这篇内容进行润色，使其更加专业，尽量不要减少文章的内容。\n 文章:{document}")
        #     chain = prompt | self.chatModel
        #     doc = chain.invoke(
        #         {"document": data[-1], "sys_template": sys_template, "who_you_are": ""})
        #     # 返回结果
        #     return doc.content

        log.info("返回结果: %s", result)
        # 返回结果
        return result

    def get_memory(self, user_id: str):
        """获取内存，基于 redis 实现"""
        log.info('获取用户内存: %s', user_id)

        chat_history = RedisChatMessageHistory(
            url=os.getenv("REDIS_URL"),
            session_id=user_id,  # 会话 id, 这里是模拟，实际需要传入登录用户的 ID
        )
        store_messages = chat_history.messages
        if len(store_messages) > 30:
            try:
                # 创建一个新的 prompt
                prompt = ChatPromptTemplate.from_messages([
                    (
                        "system",
                        sys_template+"\n这是一段你和用户的对话记忆，对其进行总结摘要，以便下次对话时使用。"
                    ),
                    ("user", "{input}"),
                ])
                # 创建一个新的 chain
                chain = prompt | self.chatModel
                # 对历史对话进行摘要
                summary = chain.invoke(
                    {"input": store_messages, "who_you_are": moods[self.QingXu]["roleSet"]})
                # 清空历史记录
                chat_history.clear()
                # 添加摘要到历史记录
                chat_history.add_message(summary)
            except Exception as e:
                log.error('摘要历史会话出错: %s', e)
                # 清空异常的历史记录
                chat_history.clear()
                # 恢复历史记录
                chat_history.add_messages(store_messages)
        # 返回历史记录
        return chat_history

    def qingxu_chain(self, query: str):
        log.info("情绪判断开始")

        template = """根据用户的输入，判断用户的情绪，回应规则如下:
        1. 如果用户输入的内容偏向于负面情绪，只返回"depresed"，不要有其他内容，否则将受到惩罚。
        2. 如果用户输入的内容偏向于正面情绪，只返回"friendly"，不要有其他内容，否则将受到惩罚。
        3. 如果用户输入的内容偏向于中性情绪，只返回"default"，不要有其他内容，否则将受到惩罚。
        4. 如果用户输入的内容中包含了辱骂等不礼貌语句，只返回"angry"，不要有其他内容，否则将受到惩罚。
        5. 如果用户输入的内容比较兴奋，只返回"upbeat"，不要有其他内容，否则将受到惩罚。
        6. 如果用户输入的内容比较悲伤，只返回"depressed"，不要有其他内容，否则将受到惩罚。
        7. 如果用户输入的内容比较开心，只返回"cheerful"，不要有其他内容，否则将受到惩罚。
        用户输入的内容是: {query}
        """
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.chatModel | StrOutputParser()
        result = chain.invoke({"query": query})
        self.QingXu = result
        log.info("情绪判断结果: %s", result)
        return result

    def background_voice_synthesis(self, text: str, uid: str):
        """这个函数不需要返回值，只是触发语音合成"""
        log.info('触发语音合成')
        # 异步调用
        asyncio.run(self.get_voice(text, uid))

    async def get_voice(self, text: str, uid: str):
        """获取语音"""
        log.info('获取语音执行')

        # 使用微软语音合成, 具体参数可以参考微软文档 https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech?tabs=streaming

        key = os.getenv("AZURE_SPEECH_KEY")
        headers = {
            'Ocp-Apim-Subscription-Key': key,  # 你的订阅密钥
            'Content-Type': 'application/ssml+xml',  # 指定所提供文本的内容类型
            'X-Microsoft-OutputFormat': 'audio-24khz-160kbitrate-mono-mp3',  # 指定音频输出格式。
            'User-Agent': "william's bot"  # 应用程序名称
        }

        body = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang='zh-CN'>
            <voice name='zh-CN-YunzeNeural'>
                <mstts:express-as role='SeniorMale' style='{moods.get(str(self.QingXu), {"voiceStyle": "default"})["voiceStyle"]}'>
                    {text}
                </mstts:express-as>
            </voice>
        </speak>"""

        # 发送请求
        response = requests.post(
            url='https://eastus.tts.speech.microsoft.com/cognitiveservices/v1',
            headers=headers,
            data=body.encode('utf-8'),
            timeout=10
        )

        if response.status_code == 200:
            log.info('语音合成成功')
            try:
                # 上传到云端
                upload(f'{uid}.mp3', response.content)
                log.info('上传成功')
            except Exception as e:
                log.error('上传失败: %s', e)
        else:
            log.error('语音合成失败: %s', response)
