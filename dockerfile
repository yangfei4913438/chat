# 使用python3.12.3-slim镜像
FROM python:3.12.3-slim

# 设置工作目录
WORKDIR /ai_server

# 拷贝当前目录下的所有文件到工作目录
COPY . .

# 设置环境变量，指定 pip 镜像地址
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple

# 安装pipenv
RUN pip install pipenv

# 安装项目的依赖项到 Docker 虚拟环境中
RUN pipenv install --deploy

# 暴露端口
EXPOSE 8000

# 设置启动命令
CMD ["python", "server.py"]