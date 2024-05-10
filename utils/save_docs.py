from langchain_core.documents import Document
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, UnstructuredExcelLoader, TextLoader
from fastapi import HTTPException, status

from utils.custom_log import log
from utils.chains import split_texts, split_documents, save_texts, get_map_reduce_chain


class SaveDocs:
    """ 保存文档的工具类 """

    def __init__(self):
        # 允许的文件类型
        self.file_extension = ['docx', 'pdf', 'xlsx', 'txt']

    def get_file_extension(self, doc_path: str):
        """获取文件扩展名"""
        return doc_path.split('.')[-1]

    def check_file_extension(self, doc_path: str) -> bool:
        """检查文件扩展名是否合法"""
        file_extension = self.get_file_extension(doc_path)
        return file_extension in self.file_extension

    def getFile(self, doc_path: str) -> str | None:
        """根据文件路径，加载文件内容"""
        loaders = {
            'docx': Docx2txtLoader,
            'pdf': PyPDFLoader,
            'xlsx': UnstructuredExcelLoader,
            'txt': TextLoader,
        }
        file_extension = self.get_file_extension(doc_path)
        loader_class = loaders.get(file_extension)
        if loader_class:
            try:
                loader = loader_class(doc_path)
                text = loader.load()
                return text
            except Exception as e:
                log.error('加载 %s 文件出错: %s', file_extension, e)
                return None
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'不支持的文件类型{file_extension}'
            )

    def splitSentences(self, doc_path: str) -> None | list[Document]:
        """ 分割文档 """
        # 获取文档内容
        full_text = self.getFile(doc_path)
        if full_text is not None:
            # 分割文档
            return split_documents(full_text)
        else:
            return None

    # 向量化与向量存储
    def save(self, doc_path: str):
        if not self.check_file_extension(doc_path):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不支持的文件类型"
            )

        documents = self.splitSentences(doc_path)
        if documents is not None:
            # 获取 map reduce 链
            reduce = get_map_reduce_chain()
            # 合并文档
            text = reduce.invoke(documents)
            log.info('合并文档后的文本: %s', text)
            # 在此分割文档
            documents_end = split_texts(text["output_text"])
            # 最终保存文档
            result = save_texts(documents_end)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="服务器出现异常，请稍后再试"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="服务器出现异常，请稍后再试"
            )
