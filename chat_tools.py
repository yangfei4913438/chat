import requests
import os

from langchain.agents import tool
from langchain_community.utilities.serpapi import SerpAPIWrapper
from langchain_community.vectorstores.qdrant import Qdrant
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings, ChatOpenAI, OpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from chat_consts import qdrant_path
from custom_log import log


@tool
def search(query: str):
    """只有需要了解实时信息或不知道的事情的时候，才会调用这个工具，用于搜索相关信息"""

    log.info("开始搜索: %s", query)

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

    log.info("返回实时搜索结果: %s", result)
    return result


@tool
def local_db(query: str):
    """不管用户询问什么问题，都要优先调用这个工具来回答。这里是本地知识库，可以查询到本地已经学习到的知识。"""

    log.info("开始查询本地数据库: %s", query)

    # 创建向量数据库
    client = Qdrant(
        client=QdrantClient(path=qdrant_path()),  # 指定向量数据库客户端
        collection_name="local_documents",  # 指定集合名称
        embeddings=OpenAIEmbeddings()  # 指定向量化工具
    )
    # 生成检索器
    retriever = client.as_retriever(search_type="mmr")

    try:
        # 获取相关文档
        result = retriever.get_relevant_documents(query)

        log.info("返回本地数据库查询结果: %s", result)

        return result
    except Exception as e:
        log.error("查询本地数据库出错了: %s", e)
        return f"本地数据库没有查到数据，你换其他工具继续查询: {query}"


@tool
def shengxiao(query: str):
    """只有做生肖配对的时候，才会调用这个工具。需要用户提供男方和女方的生肖，如果你没有这些信息，那就提示用户输入。"""

    log.info("开始查询生肖配对: %s", query)

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

    llm = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE'),
        temperature=0
    )

    chain = prompt | llm | parser

    data = chain.invoke({"query": query})

    log.info("生肖配对结果: %s", data)

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
            log.error("提取 json 出错了: %s", e)
            return "生肖配对失败, 可能是你忘记询问用户相关信息了。"
    else:
        log.error("返回数据异常: %s", result)
        return f"生肖配对查询失败, 换个工具继续查询: {query}"


@tool
def bazi_hehun(query: str):
    """只有算八字合婚的时候，才会调用这个工具。需要提供男方的姓名、出生的年月日时，女生的姓名，出生的年月日时，如果缺少这些信息则不可用。
    只有符合条件的时候才会调用这个工具。"""

    log.info("开始查询八字合婚: %s", query)

    template = """你是一个参数查询助手，根据用户输入的内容，找出相关的参数信息，并按 json 格式返回。
    json字段如下:
    - "male_name": "男方姓名, 必传字段"
    - "male_type": "男方出生日期类型，1为阳历也就是公历，0为阴历也就是农历，默认是1"
    - "male_year": "男方出生年份，例如 1990, 必传字段"
    - "male_month": "男方出生月份，例如 1, 必传字段"
    - "male_day": "男方出生天，例如 1, 必传字段"
    - "male_hours": "男方出生时，例如 12, 必传字段"
    - "male_minute": "男方出生分，例如 30，如果没有则默认为 0"
    - "female_name": "女方姓名, 必传字段"
    - "female_type": "女方出生日期类型，1为阳历也就是公历，0为阴历也就是农历，默认是1"
    - "female_year": "女方出生年份，例如 1990, 必传字段"
    - "female_month": "女方出生月份，例如 1, 必传字段"
    - "female_day": "女方出生天，例如 1, 必传字段"
    - "female_hours": "女方出生时，例如 12, 必传字段"
    - "female_minute": "女方出生分，例如 30，如果没有则默认为 0"
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

    llm = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE'),
        temperature=0
    )

    chain = prompt | llm | parser

    data = chain.invoke({"query": query})

    log.info("八字合婚查询参数: %s", data)

    request_data = {
        "api_key": os.getenv("TOOLS_MINGLI_KEY"),
        **data
    }

    result = requests.post(
        url=os.getenv("TOOLS_BAZI_HEHUN_URL"),
        data=request_data,
        timeout=10)

    if result.status_code == 200:
        try:
            result = result.json()["data"]
            data = {
                "合婚命宫": result["minggong"],
                "年支同气": result["nianqitongzhi"],
                "月令合": result["yueling"],
                "日干相合": result["rigan"],
                "天干五合": result["tiangan"],
                "子女同步": result["zinv"],
                "合婚总分": result["all_score"],
                "男方生肖": result["male_sx"],
                "女方生肖": result["female_sx"],
                "男方星座": result["male_xz"],
                "女方星座": result["female_xz"]
            }
            log.info("八字合婚最终数据: %s", data)
            return data
        except Exception as e:
            log.error("提取 json 出错了: %s", e)
            return "八字合婚查询失败, 可能是你忘记询问用户必填的相关信息了。"
    else:
        log.error("返回数据异常: %s", result)
        return f"八字合婚查询失败, 换个工具继续查询: {query}"


@tool
def weilai(query: str):
    """只有算未来运势的时候，才会调用这个工具。需要提供姓名、性别、出生的年月日时分，需要预测的年份，如果缺少这些信息则不可用。
    只有符合条件的时候才会调用这个工具。"""

    log.info("开始查询未来运势: %s", query)

    template = """你是一个参数查询助手，根据用户输入的内容，找出相关的参数信息，并按 json 格式返回。
    json字段如下:
    - "name": "姓名, 必传字段"
    - "sex": "性别 0男 1女, 必传字段"
    - "type": "历类型 0农历 1公历，默认是1"
    - "year": "出生年份 例: 1988, 必传字段"
    - "month": "男方出生月份，例如 8, 必传字段"
    - "day": "男方出生天，例如 12, 必传字段"
    - "hours": "男方出生的小时，例如 12, 必传字段"
    - "minute": "男方出生的分钟，例如 30，如果没有则默认为 0"
    - "yunshi_year": "需要测未来哪个公历年 例: 2030, 此参数只能大于等于当前公历年份。必传字段"
    - "compute_daily": "是否算每日运势 例： 1：是 2：否，非必传，不传递这个参数，默认2"
    - "sect": "流派 例：1：晚子时日柱算明天 2：晚子时日柱算当天。非必传，如果不传递这个参数，默认2 "
    - "zhen": "是否真太阳时 例：1：考虑真太阳时 2：不考虑真太阳时。 非必传，如果不传递这个参数，默认2"
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

    llm = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE'),
        temperature=0
    )

    chain = prompt | llm | parser

    data = chain.invoke({"query": query})

    log.info("未来运势查询参数: %s", data)

    request_data = {
        "api_key": os.getenv("TOOLS_MINGLI_KEY"),
        **data
    }

    result = requests.post(
        url=os.getenv("TOOLS_WEILAI_URL"),
        data=request_data,
        timeout=10)

    if result.status_code == 200:
        try:
            result = result.json()["data"]["detail_info"]
            data = {
                "四柱信息": result["sizhu_info"],
                "预测的未来年运势信息": result["yunshi_year_info"]
            }
            log.info("未来运势最终数据: %s", data)
            return data
        except Exception as e:
            log.error("提取 json 出错了: %s", e)
            return "未来运势查询失败, 可能是你忘记询问用户必填的相关信息了。"
    else:
        log.error("返回数据异常: %s", result)
        return f"未来运势查询失败, 换个工具继续查询: {query}"


@tool
def chenggu(query: str):
    """只有算称骨论命的时候，才会调用这个工具。需要提供姓名、性别、出生的年月日时，如果缺少这些信息则不可用。只有符合条件的时候才会调用这个工具。"""

    log.info("开始查询称骨论命: %s", query)

    template = """你是一个参数查询助手，根据用户输入的内容，找出相关的参数信息，并按 json 格式返回。
    json字段如下:
    - "name": "姓名, 必传字段"
    - "sex": "性别 0男 1女, 必传字段"
    - "type": "历类型 0农历 1公历，默认是1"
    - "year": "出生年份 例: 1988, 必传字段"
    - "month": "男方出生月份，例如 8, 必传字段"
    - "day": "男方出生天，例如 12, 必传字段"
    - "hours": "男方出生的小时，例如 12, 必传字段"
    - "minute": "男方出生的分钟，例如 30，如果没有则默认为 0"
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

    llm = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE'),
        temperature=0
    )

    chain = prompt | llm | parser

    data = chain.invoke({"query": query})

    log.info("称骨论命查询参数: %s", data)

    request_data = {
        "api_key": os.getenv("TOOLS_MINGLI_KEY"),
        **data
    }

    result = requests.post(
        url=os.getenv("TOOLS_CHENGGU_URL"),
        data=request_data,
        timeout=10)

    if result.status_code == 200:
        try:
            res = result.json()["data"]["chenggu"]
            data = {
                "批示": res["description"],
                "总重量": res["total_weight"],
                "几两": res["liang"],
                "几钱": res["qian"],
            }
            log.info("称骨论命最终数据: %s", data)
            return data
        except Exception as e:
            log.error("提取 json 出错了: %s", e)
            return "称骨论命查询失败, 可能是你忘记询问用户必填的相关信息了。"
    else:
        log.error("返回数据异常: %s", result)
        return f"称骨论命查询失败, 换个工具继续查询: {query}"


@tool
def zeshi(query: str):
    """只有择吉日的时候，才会调用这个工具。需要提供未来的时间范围（最长未来三个月）和要做的事情，如果缺少这些信息则不可用。只有符合条件的时候才会调用这个工具。"""

    log.info("开始择吉日的查询: %s", query)

    template = """你是一个参数查询助手，根据用户输入的内容，找出相关的参数信息，并按 json 格式返回。
    json字段如下:
    - "future": "未来时间范围 例：0.未来7天 1.未来半个月 2.未来1个月 3.未来3个月。非必须参数，默认0"
    - "incident": "要做的事情，0.迁徙|搬家 1.修造|装修 2.入宅 3.纳采|订婚|结婚 4.嫁娶|领证 5.求嗣|破腹产 6.纳财 7.开市 8.交易 9.置产 10.动土 11.出行
                   12.安葬 13.祭祀 14.祈福 15.沐浴 16.订盟 17.纳婿 18.修坟 19.破土 20.安葬 21.立碑 22.开生坟 23.合寿木 24.入殓 25.移柩 26.伐木 27.掘井 
                   28.挂匾 29.栽种 30.入学 31.理发 32.会亲友 33.赴任 34.求医 35.治病。非必须参数，默认0"
    只返回 json 格式的数据。不要返回其他内容。
    用户输入: {query}
    """
    prompt = ChatPromptTemplate.from_template(template=template)
    parser = JsonOutputParser()
    # 根据输入内容，生成新的模板
    # partial主要是将部分变量在提示词中实例化
    prompt = prompt.partial(
        format_instructions=parser.get_format_instructions())

    llm = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE'),
        temperature=0
    )

    chain = prompt | llm | parser

    data = chain.invoke({"query": query})

    log.info("择吉日的查询参数: %s", data)

    request_data = {
        "api_key": os.getenv("TOOLS_MINGLI_KEY"),
        **data
    }

    result = requests.post(
        url=os.getenv("TOOLS_ZESHI_URL"),
        data=request_data,
        timeout=10)

    if result.status_code == 200:
        try:
            res = result.json()["data"]
            summarize = res["base_info"]["summarize"]
            detail_list = res["detail_info"]

            data = {
                "概要": summarize,
                "吉日列表": [
                    {
                        "阳历": item["yangli"],
                        "阴历": item["yinli"],
                        "本日宜": item["yi"],
                        "本日忌": item["ji"],
                    }
                    for item in detail_list
                ],
            }
            log.info("择吉日最终数据: %s", data)
            return data
        except Exception as e:
            log.error("提取 json 出错了: %s", e)
            return "择吉日查询失败, 可能是你忘记询问用户必填的相关信息了。"
    else:
        log.error("返回数据异常: %s", result)
        return f"择吉日查询失败, 换个工具继续查询: {query}"


@tool
def qiming(query: str):
    """只有在起名的时候，才会调用这个工具。起名需要提供，被起名的人的姓氏和性别，如果缺少这些信息则不可用。只有符合条件的时候才会调用这个工具。"""

    log.info("开始起名的查询: %s", query)

    template = """你是一个参数查询助手，根据用户输入的内容，找出相关的参数信息，并按 json 格式返回。
    json字段如下:
    - "surname": "姓氏, 必传字段"
    - "sex": "性别，0 表示男性，1 表示女性, 必传字段"
    如果必传字段缺少，那就提示用户告诉你这些内容。如果用户不仅提供了被起名人的父亲的姓氏，还提供了被起名人的母亲的姓氏，那就以父亲的姓氏为准。
    只返回 json 格式的数据。不要返回其他内容。
    用户输入: {query}
    """
    prompt = ChatPromptTemplate.from_template(template=template)
    parser = JsonOutputParser()
    # 根据输入内容，生成新的模板
    # partial主要是将部分变量在提示词中实例化
    prompt = prompt.partial(
        format_instructions=parser.get_format_instructions())

    llm = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE'),
        temperature=0
    )

    chain = prompt | llm | parser

    data = chain.invoke({"query": query})

    log.info("起名的查询参数: %s", data)

    # 除了需要语义分析的参数，其他参数都是固定写在这里，不要传给大模型分析
    request_data = {
        "api_key": os.getenv("TOOLS_MINGLI_KEY"),
        **data,
        "page": 1,
        "limit": 50,
    }

    result = requests.post(
        url=os.getenv("TOOLS_QIMING_URL"),
        data=request_data,
        timeout=10)

    if result.status_code == 200:
        try:
            res = result.json()["data"]
            data = res["list"]
            log.info("起名的最终数据: %s", data)
            return f"{data}, 从这些名字中，选择三个好记忆的名字，如果用户提供了被起名人母亲的姓氏，那么名字尽量选择和被起名人母亲的姓氏的五行属性有关联的名字。最后，分别带上每个名字的详细含义、五行属性，五行的含义，以及选中这个名字的具体理由，返回给用户。"
        except Exception as e:
            log.error("提取 json 出错了: %s", e)
            return "起名失败, 可能是你忘记询问用户必填的相关信息了。"
    else:
        log.error("返回数据异常: %s", result)
        return f"起名查询失败, 换个工具继续查询: {query}"


@tool
def bazi_cesuan(query: str):
    """只有做八字测算的时候，才会调用这个工具。需要用户的名字、用户的性别，用户的出生年月日小时，如果你没有这些信息，那就提示用户输入。
    只有符合条件的时候才会调用这个工具。"""

    log.info("开始查询八字测算: %s", query)

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

    llm = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE'),
        temperature=0
    )

    chain = prompt | llm | parser

    data = chain.invoke({"query": query})

    log.info("八字测算参数: %s", data)

    request_data = {
        "api_key": os.getenv("TOOLS_MINGLI_KEY"),
        **data
    }

    result = requests.post(
        url=os.getenv("TOOLS_BAZI_URL"),
        data=request_data,
        timeout=10)

    if result.status_code == 200:
        log.info("====返回数据=====")
        log.info(result.json())
        return result.json()["data"]
    else:
        log.error("返回数据异常: %s", result)
        return f"八字测算查询失败, 换个工具继续查询: {query}"


@tool
def yaogua(query: str):
    """只有用户想要算卦、抽签，摇卦的时候，才会使用这个工具"""

    log.info("开始查询摇卦: %s", query)

    result = requests.post(
        url=os.getenv("TOOLS_YAOGUA_URL"),
        data={"api_key": os.getenv("TOOLS_MINGLI_KEY")},
        timeout=10
    )

    if result.status_code == 200:
        try:
            res = result.json()["data"]
            data = {
                "易经第几卦": res["id"],
                "卦名": res["common_desc1"],
                "象曰": res["common_desc2"],
                "解卦": res["common_desc3"],
                "事业": res["shiye"],
                "经商": res["jingshang"],
                "求名": res["qiuming"],
                "外出": res["waichu"],
                "婚恋": res["hunlian"],
                "决策": res["juece"]
            }

            log.info("摇卦最终数据: %s", data)

            return data
        except Exception as e:
            log.error("提取 json 出错了: %s", e)
            return "摇卦失败，请告诉用户稍后再试"
    else:
        log.error("返回数据异常: %s", result)
        return f"摇卦查询失败, 换个工具继续查询: {query}"


@tool
def jiuxing(query: str):
    """只有用户想要算九星运势的时候才会使用这个工具，需要输入用户的姓名、性别、出生的年月日时，如果缺少用户的姓名、性别和出生年月日则不可用。
    只有符合条件的时候才会调用这个工具。"""

    log.info("开始查询九星运势: %s", query)

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

    llm = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE'),
        temperature=0
    )

    chain = prompt | llm | parser

    data = chain.invoke({"query": query})

    log.info("九星运势查询参数: %s", data)

    request_data = {
        "api_key": os.getenv("TOOLS_MINGLI_KEY"),
        **data
    }

    result = requests.post(
        url=os.getenv("TOOLS_JIUXING_URL"),
        data=request_data,
        timeout=10)

    if result.status_code == 200:
        log.info("====返回数据=====")
        log.info(result.json())
        try:
            res = result.json()
            return res["data"]["jiuxing"]
        except Exception as e:
            log.error("提取 json 出错了: %s", e)
            return "九星运势查询失败, 可能是你忘记询问用户必填的相关信息了。"
    else:
        log.error("返回数据异常: %s", result)
        return f"九星运势查询失败, 换个工具继续查询: {query}"


@tool
def jiemeng(query: str):
    """只有用户想要解梦的时候才会使用这个工具,需要输入用户梦境的内容，如果缺少用户梦境的内容则不可用。"""

    log.info("开始查询解梦: %s", query)

    llm = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE'),
        temperature=0
    )

    prompt = PromptTemplate.from_template("根据内容提取1个关键词，只返回关键词，内容为:{topic}")

    prompt_value = prompt.invoke({"topic": query})

    keyword = llm.invoke(prompt_value)

    log.info("提取的关键词: %s", keyword)

    result = requests.post(
        url=os.getenv("TOOLS_JIEMENG_URL"),
        data={
            "api_key": os.getenv("TOOLS_MINGLI_KEY"),
            "title_zhougong": keyword
        },
        timeout=10
    )

    if result.status_code == 200:
        log.info("====返回数据=====")
        log.info(result.json())
        res = result.json()
        return res["data"][-3:]
    else:
        log.error("返回数据异常: %s", result)
        return f"解梦查询失败, 换个工具继续查询: {query}"
