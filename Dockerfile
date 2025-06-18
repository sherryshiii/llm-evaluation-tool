FROM python:3.13-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建日志目录
RUN mkdir -p logs runtime

# 暴露端口
EXPOSE 7860

# 设置 Python 环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "main.py"] 