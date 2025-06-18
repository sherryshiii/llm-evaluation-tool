# LLM 响应比较工具

这是一个用于比较不同 LLM 模型响应的工具，支持单条比较和批量比较功能。

## 项目结构

```
llm_eval/
├── main.py              # 主程序入口
├── config.py            # 配置文件
├── llm.yaml            # LLM API 配置
├── llm_client.py       # LLM API 客户端
├── ui_shared.py        # 共享工具函数
├── ui_single.py        # 单条比较界面
├── ui_table.py         # 批量比较界面
├── table_demo.xlsx     # 批量比较示例数据
├── requirements.txt    # 项目依赖
├── Dockerfile          # Docker 构建文件
├── utils/              # 工具函数目录
│   ├── __init__.py
│   ├── comparator.py   # 比较器实现
│   ├── log.py         # 日志工具
│   └── resp_parser.py # 响应解析器
├── logs/              # 日志目录
└── runtime/           # 运行时文件目录
```

## 本地运行（推荐）

1. 创建并激活虚拟环境：
```bash
# 创建虚拟环境
python -m venv venv

# 在 macOS/Linux 上激活虚拟环境
source venv/bin/activate

# 在 Windows 上激活虚拟环境
# .\venv\Scripts\activate
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行应用：
```bash
python main.py
```

4. 在浏览器中打开显示的URL（通常是 http://127.0.0.1:7860）

5. 完成后退出虚拟环境：
```bash
deactivate
```

## Docker 运行

### 开发环境运行

我们提供了便捷的开发环境启动脚本，只需执行：

```bash
chmod +x ./run-dev.sh
./run-dev.sh
```

该脚本会：
- 首次运行时自动构建 Docker 镜像
- 仅在 requirements.txt 发生变化时重新构建镜像
- 启动开发模式（dev.py），支持代码热更新
- 自动检测并重启程序（无需重启容器）
- 自动挂载当前目录到容器中
- 映射 7860 端口到宿主机

开发模式特性：
- 自动监控所有 .py 文件的变化
- 文件变更时自动重启应用
- 控制台实时显示文件变化和重启信息
- 支持优雅退出（Ctrl+C）

### 手动构建与运行

如果需要手动控制 Docker 构建和运行过程：

1. 构建镜像
```bash
docker build -t llm-eval-dev .
```

2. 运行容器
```bash
docker run --rm -v $(pwd):/app -p 7860:7860 --name llm-eval-dev llm-eval-dev
```

### 注意事项

- 开发时推荐使用 `run-dev.sh` 脚本，可以避免不必要的镜像重建
- 代码修改会实时同步到容器中，无需重启容器
- 如果修改了 requirements.txt，脚本会自动重新构建镜像
- 容器在退出时会自动删除，不会残留在系统中
- 如需强制重新构建镜像，可以执行：
  ```bash
  docker build -t llm-eval-dev . && ./run-dev.sh
  ```

## 配置说明

1. 在 `llm.yaml` 中配置您的 LLM API 密钥和其他设置
2. 日志文件将保存在 `logs` 目录下

## 功能特点

- 支持多个 LLM 平台的模型比较
- 实时日志显示
- 单条和批量比较模式
- 友好的 Web 界面
