
import os
from fastapi import HTTPException, UploadFile, status
from langchain_text_splitters import HTMLHeaderTextSplitter
from utils.custom_log import log
from utils.save_docs import SaveDocs
from utils.chains import save_texts, split_texts, get_stuff_chain


async def save_file(file: UploadFile):
    """ 添加文件，直接学习文件中的数据 """
    log.info("添加文件 %s", file.filename)

    # 实例化保存文档的工具类
    save_docs = SaveDocs()
    # 文件类型检查
    if not save_docs.check_file_extension(file.filename):
        log.error("不支持的文件类型")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型"
        )

    # 存储PDF文件到临时文件
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as out_file:
        out_file.write(await file.read())

    try:
        # 保存文档
        save_docs.save(temp_file_path)

        # 删除临时文件
        os.remove(temp_file_path)

        log.info("文件保存成功")
        return {"ok": "文件保存成功"}
    except Exception as e:
        # 删除临时文件
        os.remove(temp_file_path)
        raise e


def add_url(url: str):
    """ 添加网页链接，直接学习网页上的数据 """
    log.info("保存网页 %s", url)

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

    chain = get_stuff_chain()

    docs = chain.invoke(documents)

    log.info('合并文档后的文本: %s', docs)

    # 在此分割文档
    texts = split_texts(docs["output_text"])

    # 保存文档
    result = save_texts(texts)

    if not result:
        log.error("保存网页失败")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="保存网页失败"
        )
    else:
        log.info("保存网页成功")
        return {"ok": "保存网页成功"}
