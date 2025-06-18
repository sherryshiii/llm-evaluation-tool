import asyncio
import time
import logging
import json
from typing import List, Dict
from openai import AsyncOpenAI
from config import get_model_by_key, get_platform_concurrent_config
import gradio as gr

logger = logging.getLogger("req")

# 初始化所有平台的信号量
platform_semaphores = {
    platform: asyncio.Semaphore(concurrent)
    for platform, concurrent in get_platform_concurrent_config().items()
}

async def request(model: Dict, messages: List[Dict[str, str]], response_format="JSON", temperature=0, state=None) -> Dict:
    async with platform_semaphores[model['platform']['key']]:
        try:
            start_time = time.time()
            
            # 创建客户端，设置超时时间为20秒
            client = AsyncOpenAI(
                api_key=model['platform']['api_key'], 
                base_url=model['platform']['url'],
                timeout=20.0
            )
            
            # 准备请求数据
            request_data = {
                "model": model['model'],
                "messages": messages,
                "temperature": max(0.1, temperature) if model['platform']['key'] == "baidu" else temperature
            }
            
            # 只有当选择 JSON 格式时才添加 response_format
            if response_format == "JSON":
                request_data["response_format"] = {"type": "json_object"}
            
            raw_response = await client.chat.completions.with_raw_response.create(**request_data)
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            response = raw_response.parse()  # 获取解析后的响应
            response_content = response.choices[0].message.content

            usage = response.usage if hasattr(response, "usage") else None
            input_tokens = usage.prompt_tokens if usage else None
            output_tokens = usage.completion_tokens if usage else None

            raw_response_text = raw_response.text
            
            logger.info(json.dumps({
                "url": f"{client.base_url}chat/completions",
                "request": request_data,
                "response": json.loads(raw_response_text),
                "elapsed_ms": elapsed_ms
            }, ensure_ascii=False))

            return {
                "model_key": f"{model['platform']['key']}-{model['model']}",
                "time": elapsed_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "content": response_content,
                "state": state
            }
        except Exception as e:
            # 记录错误日志
            logger.error(f"Request {client.base_url} with Data: {json.dumps(request_data, ensure_ascii=False)} Error: {str(e)}")
            return {
                "model_key": f"{model['platform']['key']}-{model['model']}",
                "time": None,
                "input_tokens": None,
                "output_tokens": None,
                "content": str(e),
                "state": state
            }

async def multi_request(tasks: List[Dict], progress: gr.Progress) -> List[Dict]:
    """
    并发处理多个 LLM 请求任务
    
    Args:
        tasks: 任务列表，每个任务是一个字典，包含以下字段：
            - sys_prompt: 系统提示词
            - user_prompt: 用户提示词
            - model_key: 模型标识
            - response_format: 响应格式
            - temperature: 温度参数
        progress: Gradio 进度条对象，用于显示任务执行进度
    
    Returns:
        List[Dict]: 每个任务的执行结果列表，保持输入顺序
    """
    if not tasks:
        return []

    request_tasks = []
    for i, task in enumerate(tasks):
        messages = []
        if task.get('sys_prompt'):
            messages.append({"role": "system", "content": task['sys_prompt']})
        if task.get('user_prompt'):
            messages.append({"role": "user", "content": task['user_prompt']})
            
        request_tasks.append(
            request(
                get_model_by_key(task['model_key']), 
                messages, 
                task['response_format'],
                task['temperature'],
                state=i
            )
        )
    
    results = []
    for i, task in enumerate(asyncio.as_completed(request_tasks)):
        result = await task
        results.append(result)
        progress((i + 1) / len(request_tasks))
    
    # 根据 state 排序结果
    results.sort(key=lambda x: x["state"])
    
    return [
        {
            "model_key": r["model_key"],
            "time": r["time"],
            "input_tokens": r["input_tokens"],
            "output_tokens": r["output_tokens"],
            "content": r["content"]
        }
        for r in results
    ]

