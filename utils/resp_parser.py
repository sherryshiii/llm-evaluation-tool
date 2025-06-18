import json
import logging
import importlib
import aiohttp
from json_repair import repair_json
import asyncio
import inspect
from typing import List, Tuple

logger = logging.getLogger("req")

http_semaphore = asyncio.Semaphore(10)

PARSER_FUNCTIONS = {
    "fix_json": "JSON修复",
    "simple_fix_json": "简易JSON修复",
    "clean_location": "地区清洗",
    "clean_address_json": "多地区JSON清洗"
}

def fix_json(text: str) -> dict:
    """
    修复不规范的JSON字符串并解析为字典
    
    Args:
        text: 可能包含JSON的文本字符串
        
    Returns:
        dict: 解析后的JSON字典，如果解析失败则返回空字典
    """
    try:
        # 移除可能的markdown代码块标记
        text = text.replace("```json", "").replace("```", "").strip()
        # 使用json_repair修复并解析JSON
        repaired_json = repair_json(text)
        return json.loads(repaired_json)
    except Exception as e:
        return {}

def simple_fix_json(text: str) -> dict:
    """
    对JSON字符串进行简单的清洗和修复
    
    Args:
        text: 可能包含JSON的文本字符串
        
    Returns:
        dict: 解析后的JSON字典，如果解析失败则返回空字典
    """
    try:
        # 移除可能的markdown代码块标记
        text = text.replace("```json", "").replace("```", "").strip()
        # 直接解析JSON
        return json.loads(text)
    except Exception as e:
        return {}

async def clean_location(text: str) -> dict:
    """
    清洗地区信息，提取并标准化省市区信息
    
    Args:
        text: 包含地区信息的JSON字符串
        
    Returns:
        dict: 清洗后的地区信息字典
    """
    async with http_semaphore:
        # 首先修复并解析JSON
        location_json = simple_fix_json(text)
        
        if not location_json:
            return {}
        
        # 提取省市区信息
        province = location_json.get("province", "").strip()
        city = location_json.get("city", "").strip()
        district = location_json.get("district", "").strip()
        
        # 调用地区清洗API
        try:
            url = 'https://api.yunque123.cn/v1/publicapi/ai/location-analyze'
            
            # 准备请求数据
            data = {
                'province': province,
                'city': city,
                'district': district
            }
            
            # 发送异步POST请求
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    response.raise_for_status()
                    result = await response.json()
            
            # 记录请求和响应信息
            logger.info(json.dumps({
                "url": url,
                "request": data,
                "response": result
            }, ensure_ascii=False))
            
            if result['status'] == 'ok' and result['data']:
                location_data = result['data'][0]
                # 更新原始JSON中的省市区信息，如果API返回为空则保持原值
                location_json["province"] = location_data["province"]['name'] if type(location_data["province"]) is dict else location_data['province']
                location_json["city"] = location_data["city"]['name'] if type(location_data["city"]) is dict else location_data['city']
                location_json["district"] = location_data["district"]['name'] if type(location_data["district"]) is dict else location_data['district']
        except Exception as e:
            # 记录错误信息
            logger.error(json.dumps({
                "url": url,
                "request": data,
                "error": str(e)
            }, ensure_ascii=False))
            # 请求失败时保持原始数据不变
            pass
        
        return location_json

async def process_responses(contents: List[str], parser_type: str) -> List[str]:
    """
    异步处理多个响应内容
    
    Args:
        contents: 响应内容列表
        parser_type: 解析器类型
        
    Returns:
        List[str]: 处理后的响应列表
    """
    if parser_type == "":
        return contents

    module = importlib.import_module("utils.resp_parser")
    parser_func = getattr(module, parser_type, None)
    
    if inspect.iscoroutinefunction(parser_func):
        # 如果是异步函数，使用异步方式处理
        tasks = [parser_func(content) for content in contents]
        results = await asyncio.gather(*tasks)
        return [
            json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
            for result in results
        ]
    else:
        # 如果是同步函数，直接处理
        results = [parser_func(content) for content in contents]
        return [
            json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
            for result in results
        ]

async def clean_address_json(text: str) -> dict:
    """
    修复JSON并清洗其中的地区信息
    
    Args:
        text: 包含JSON的文本字符串
        
    Returns:
        dict: 处理后的JSON字典
    """
    # 首先修复JSON
    data = fix_json(text)
    if not data:
        return {}
    
    # 检查并处理行政地址字段
    if "行政地址" in data and isinstance(data["行政地址"], list):
        cleaned_locations = []
        for location in data["行政地址"]:
            # 转换字段名以匹配clean_location函数的预期
            location_data = {
                "province": location.get("省", ""),
                "city": location.get("市", ""),
                "district": location.get("区县", "")
            }
            
            # 清洗地区信息
            cleaned = await clean_location(json.dumps(location_data))
            if cleaned:
                # 转换回原始字段名
                cleaned_locations.append({
                    "省": cleaned.get("province", ""),
                    "市": cleaned.get("city", ""),
                    "区县": cleaned.get("district", "")
                })
        
        # 更新原始数据中的地址信息
        if cleaned_locations:
            data["行政地址"] = cleaned_locations
    
    return data