import requests
import json
import os

from langchain.agents import tool
from langchain_community.utilities.serpapi import SerpAPIWrapper
from langchain_community.vectorstores.qdrant import Qdrant
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings, ChatOpenAI, OpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from chat_consts import qdrant_path


@tool
def search(query: str):
    """只有需要了解实时信息或不知道的事情的时候，才会调用这个工具，用于搜索相关信息"""
    # 定义搜索参数
    params = {
        "engine": "google",
        "google_domain": "google.com",
        "gl": "us",
        "hl": "zh-cn"
    }
    # 创建 SerpAPIWrapper 对象
    serpapi = SerpAPIWrapper(params=params)
    # 调用搜索方法
    result = serpapi.run(query)
    print("实时搜索结果:", result)
    return result


@tool
def local_db(query: str):
    """不管用户询问什么问题，都要优先调用这个工具来回答。这里是本地知识库，可以查询到本地已经学习到的知识。"""

    print("----------查询本地数据库:", query)

    # 创建向量数据库
    client = Qdrant(
        client=QdrantClient(path=qdrant_path()),  # 指定向量数据库客户端
        collection_name="local_documents",  # 指定集合名称
        embeddings=OpenAIEmbeddings()  # 指定向量化工具
    )
    # 生成检索器
    retriever = client.as_retriever(search_type="mmr")
    # 获取相关文档
    result = retriever.get_relevant_documents(query)
    # 返回结果
    return result


@tool
def shengxiao(query: str):
    """只有做生肖配对的时候，才会调用这个工具。需要用户提供男方和女方的生肖，如果你没有这些信息，那就提示用户输入。"""

    template = """你是一个参数查询助手，根据用户输入的内容，找出相关的参数信息，并按 json 格式返回。
    json字段如下:
    - "shengxiao_male": "男方出生月 例：鼠 牛 虎 兔 龙 蛇 马 羊 猴 鸡 狗 猪"
    - "shengxiao_female": "女方出生月 例：鼠 牛 虎 兔 龙 蛇 马 羊 猴 鸡 狗 猪"
    只返回 json 格式的数据。不要返回其他内容。
    用户输入: {query}
    """
    prompt = ChatPromptTemplate.from_template(template=template)
    parser = JsonOutputParser()
    # partial主要是将部分变量在提示词中实例化
    prompt = prompt.partial(
        format_instructions=parser.get_format_instructions())

    chain = prompt | ChatOpenAI(temperature=0) | parser

    data = chain.invoke({"query": query})

    print("生肖配对结果:", data)

    request_data = {
        "api_key": os.getenv("TOOLS_MINGLI_KEY"),
        **data
    }

    result = requests.post(
        url=os.getenv('TOOLS_SHENGXIAO_URL'),
        data=request_data,
        timeout=10
    )

    if result.status_code == 200:
        print("====返回数据=====")
        print(result.json())
        try:
            data = result.json()
            return data["data"]["description"]
        except Exception as e:
            print("提取 json 出错了:", e)
            return "生肖配对失败, 可能是你忘记询问用户相关信息了。"
    else:
        return "技术错误，请告诉用户稍后再试。"


@tool
def bazi_cesuan(query: str):
    """只有做八字测算的时候，才会调用这个工具。需要用户的名字、用户的性别，用户的出生年月日小时，如果你没有这些信息，那就提示用户输入。
    只有符合条件的时候才会调用这个工具。"""

    template = """你是一个参数查询助手，根据用户输入的内容，找出相关的参数信息，并按 json 格式返回。
    json字段如下:
    - "name": "姓名, 必传字段"
    - "sex": "性别，0 表示男性，1 表示女性, 必传字段"
    - "type": "日期类型，1为阳历也就是公历，0为阴历也就是农历，默认是1"
    - "year": "年份，例如 1990, 必传字段"
    - "month": "月份，例如 1, 必传字段"
    - "day": "天，例如 1, 必传字段"
    - "hours": "时，例如 12, 必传字段"
    - "minute": "分，例如 30，如果没有则默认为 0"
    - "sect": "流派 例：1：晚子时日柱算明天 2：晚子时日柱算当天, 默认为 1"
    - "zhen": "是否真太阳时 例：1：考虑真太阳时 2：不考虑真太阳时, 默认为 2"
    - "province": "省份, 例如：广东省，非必传，但是如果考虑真太阳时，省和市都必传"
    - "city": "城市, 例如：广州市。 非必传，但是如果考虑真太阳时，省和市都必传"
    - "lang": "多语言：zh-cn 、en-us 非必传，如果不传递这个参数，默认为 zh-cn"
    如果必传字段缺少，那就提示用户告诉你这些内容。
    只返回 json 格式的数据。不要返回其他内容。
    用户输入: {query}
    """
    prompt = ChatPromptTemplate.from_template(template=template)
    parser = JsonOutputParser()
    # 根据输入内容，生成新的模板
    # partial主要是将部分变量在提示词中实例化
    prompt = prompt.partial(
        format_instructions=parser.get_format_instructions())

    chain = prompt | ChatOpenAI(temperature=0) | parser

    data = chain.invoke({"query": query})

    print("八字测算结果:", data)

    request_data = {
        "api_key": os.getenv("TOOLS_MINGLI_KEY"),
        **data
    }

    result = requests.post(
        url=os.getenv("TOOLS_BAZI_URL"),
        data=request_data,
        timeout=10)

    if result.status_code == 200:
        print("====返回数据=====")
        print(result.json())
        try:
            result = result.json()
            return result["data"]
        except Exception as e:
            print("提取 json 出错了:", e)
            return "八字查询失败, 可能是你忘记询问用户必填的相关信息了。"
    else:
        return "技术错误，请告诉用户稍后再试。"


@tool
def yaogua(query: str):
    """只有用户想要算卦、抽签，摇卦的时候，才会使用这个工具"""

    result = requests.post(
        url=os.getenv("TOOLS_YAOGUA_URL"),
        data={"api_key": os.getenv("TOOLS_MINGLI_KEY")},
        timeout=10
    )

    if result.status_code == 200:
        print("====返回数据=====")
        print(result.json())
        try:
            # 解码 JSON 字符串为 Python 对象
            result = json.loads(result.text)

            # 删除属性
            if 'image' in result["data"]:
                print("卦图片:", result["data"]["image"])
                del result["data"]['image']
                return result["data"]

            return result["data"]

        except Exception as e:
            print("提取 json 出错了:", e)
            return "占卜失败"
    else:
        return "技术错误，请告诉用户稍后再试。"


@tool
def jiemeng(query: str):
    """只有用户想要解梦的时候才会使用这个工具,需要输入用户梦境的内容，如果缺少用户梦境的内容则不可用。"""

    llm = OpenAI(temperature=0)

    prompt = PromptTemplate.from_template("根据内容提取1个关键词，只返回关键词，内容为:{topic}")

    prompt_value = prompt.invoke({"topic": query})

    keyword = llm.invoke(prompt_value)

    print("提取的关键词:", keyword)

    result = requests.post(
        url=os.getenv("TOOLS_JIEMENG_URL"),
        data={
            "api_key": os.getenv("TOOLS_MINGLI_KEY"),
            "title_zhougong": keyword
        },
        timeout=10
    )

    if result.status_code == 200:
        print("====返回数据=====")
        print(result.json())
        result = result.json()
        return result["data"][-3:]
    else:
        return "技术错误，请告诉用户稍后再试。"
