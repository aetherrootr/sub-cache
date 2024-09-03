# 使用Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将当前目录下的所有文件复制到工作目录
COPY . .

# 安装依赖
RUN pip install requests flask

# 设置环境变量（可以在运行容器时覆盖）
ENV FETCH_URL https://www.bilibili.com/
ENV FETCH_INTERVAL 600

# 暴露端口
EXPOSE 8080

# 运行 Python 脚本
CMD ["python", "app.py"]
