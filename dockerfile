# 使用python3.12.3-slim镜像
FROM python:3.12.3-slim

# 设置工作目录
WORKDIR /ai_server

# 拷贝当前目录下的所有文件到工作目录
COPY . .

# 安装pipenv
RUN pip install pipenv

# 安装依赖
RUN pipenv sync --system

# 暴露端口
EXPOSE 8000

# 设置启动命令
CMD ["python", "server.py"]