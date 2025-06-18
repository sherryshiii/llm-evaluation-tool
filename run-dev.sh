#!/bin/bash

IMAGE_NAME="llm-eval-dev"
CONTAINER_NAME="llm-eval-dev"

# 检查镜像是否存在
if ! docker images $IMAGE_NAME | grep -q $IMAGE_NAME; then
    echo "镜像不存在，开始构建..."
    docker build -t $IMAGE_NAME .
else
    # 检查容器中的 requirements.txt 是否与当前文件一致
    CONTAINER_ID=$(docker create $IMAGE_NAME)
    if ! docker cp $CONTAINER_ID:/app/requirements.txt /tmp/requirements.txt.container >/dev/null 2>&1; then
        echo "无法从容器中获取 requirements.txt，重新构建镜像..."
        docker build -t $IMAGE_NAME .
    elif ! diff requirements.txt /tmp/requirements.txt.container >/dev/null 2>&1; then
        echo "requirements.txt 有更新，重新构建镜像..."
        docker build -t $IMAGE_NAME .
    else
        echo "使用现有镜像..."
    fi
    rm -f /tmp/requirements.txt.container
    docker rm $CONTAINER_ID >/dev/null 2>&1
fi

# 检查并清理已存在的同名容器
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "清理已存在的同名容器..."
    docker rm -f $CONTAINER_NAME >/dev/null 2>&1
fi

# 运行开发环境容器
echo "启动开发模式容器..."
docker run -it --rm \
    --name $CONTAINER_NAME \
    -p 7860:7860 \
    -v $(pwd):/app \
    $IMAGE_NAME \
    python dev.py