# 使用预封装好的 chain
from langchain.chains.summarize import load_summarize_chain
from langchain_openai import ChatOpenAI
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores.qdrant import Qdrant
from langchain_openai import OpenAIEmbeddings


from utils.custom_log import log
from chat_consts import qdrant_path


def get_stuff_chain(verbose: bool = False):
    """ 获取一个预封装好的 stuff chain，用于小文本的处理"""
    llm = ChatOpenAI(temperature=0, model="gpt-4-1106-preview")
    stuff_chain = load_summarize_chain(
        llm=llm,
        chain_type="stuff",
        verbose=verbose
    )
    return stuff_chain


def get_map_reduce_chain(token_max: int = 4000, verbose: bool = False):
    """ 获取一个预封装好的 map reduce chain，用于大文本的处理"""
    llm = ChatOpenAI(temperature=0, model="gpt-4-1106-preview")
    map_reduce_chain = load_summarize_chain(
        llm=llm,
        chain_type="map_reduce",
        token_max=token_max,  # 限制 token 数量
        verbose=verbose
    )
    return map_reduce_chain


def split_texts(text: str) -> list[str]:
    """ 获取文档列表 """
    # 定义一个文本切割器
    text_splitter = CharacterTextSplitter(
        chunk_size=4000,  # 每个分割块的大小, 太小会导致分割块过多，大文件的语义处理会变慢
        chunk_overlap=100,  # 分割块之间的重叠大小
        length_function=len,  # 用于计算文本长度的函数
        add_start_index=True,  # 是否在分割块中添加起始索引
    )
    texts = text_splitter.split_text(text)
    return texts


def split_documents(text: str) -> list[Document]:
    """ 获取文档列表 """
    # 定义一个文本切割器
    text_splitter = CharacterTextSplitter(
        chunk_size=4000,  # 每个分割块的大小, 太小会导致分割块过多，大文件的语义处理会变慢
        chunk_overlap=100,  # 分割块之间的重叠大小
        length_function=len,  # 用于计算文本长度的函数
        add_start_index=True,  # 是否在分割块中添加起始索引
    )
    documents = text_splitter.split_documents(text)
    return documents


def save_texts(texts: list[str]) -> bool:
    """ 保存文档到向量数据库 """
    try:
        embedding = OpenAIEmbeddings(model="text-embedding-3-small")
        # 引入向量数据库
        Qdrant.from_texts(
            texts=texts,
            embedding=embedding,
            path=qdrant_path(),
            collection_name="local_documents"
        )
        return True
    except Exception as exc:
        log.error('向量化与向量存储出错: %s', exc)
        return False


def save_documents(documents: list[Document]) -> bool:
    """ 保存文档到向量数据库 """
    try:
        embedding = OpenAIEmbeddings(model="text-embedding-3-small")
        # 引入向量数据库
        Qdrant.from_documents(
            documents=documents,
            embedding=embedding,
            path=qdrant_path(),
            collection_name="local_documents"
        )
        return True
    except Exception as exc:
        log.error('向量化与向量存储出错: %s', exc)
        return False
