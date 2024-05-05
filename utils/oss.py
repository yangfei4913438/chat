# -*- coding: utf-8 -*-
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider

# 从环境变量中获取访问凭证。运行本代码示例之前，请确保已设置环境变量 OSS_ACCESS_KEY_ID 和 OSS_ACCESS_KEY_SECRET
auth = oss2.ProviderAuth(EnvironmentVariableCredentialsProvider())


def upload(name: str, file: bytes):
    """用于上传文件到阿里云OSS"""
    # yourEndpoint填写Bucket所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint填写为
    # https://help.aliyun.com/zh/oss/user-guide/regions-and-endpoints?spm=a2c4g.11186623.0.0.d19d65bb9ajNC6
    # 填写Bucket名称。
    bucket = oss2.Bucket(
        auth=auth,
        endpoint='https://oss-cn-shanghai.aliyuncs.com',
        bucket_name='yangfei-wiki'
    )

    try:
        # 填写Object完整路径。Object完整路径中不能包含Bucket名称。
        bucket.put_object(f'audio/{name}', file)
    except Exception as e:
        print('上传失败:', e)
