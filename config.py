import yaml
from typing import Dict

CONFIG_FILE = 'llm.yaml'

# 加载配置文件
def load_config():
    """加载配置文件"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_all_models():
    """获取所有模型列表"""
    config = load_config()
    platforms = config['platforms']
    
    # 构造所有模型的列表
    all_models = []
    for platform_key, platform_info in platforms.items():
        for model_info in platform_info['models']:
            all_models.append({
                'showname': f"{platform_info['name']}-{model_info['showname']}",
                'value': f"{platform_key}-{model_info['model']}",
                'price': model_info['price']
            })
    
    return all_models

def get_models_by_price(price):
    """根据价格获取所有符合条件的模型值"""
    all_models = get_all_models()
    return [model['value'] for model in all_models if model['price'] == price]

def get_all_model_values():
    """获取所有模型的值列表"""
    all_models = get_all_models()
    return [model['value'] for model in all_models]

def get_model_by_key(platform_model: str) -> dict:
    """
    根据模型key获取模型信息
    例如：'volcengine-doubao-1-5-lite-32k-250115' -> {'showname': 'doubao-1.5-lite', 'model': 'doubao-1-5-lite-32k-250115', 'platform': {'url': 'https://api.volcengine.com/v1', 'api_key': 'sk-06be4a7972884a03b1cc0b99d99e7fcd'}}
    """
    config = load_config()
    platforms = config['platforms']

    platform_name, model_name = platform_model.split('-', 1)
        
    for model_info in platforms[platform_name]['models']:
        if model_info['model'] == model_name:
            result = model_info.copy()
            result['platform'] = platforms[platform_name]
            result['fullname'] = f"{platforms[platform_name]['name']}-{model_info['showname']}"
            result.pop('models', None)
            return result
            
    return None

def get_platform_concurrent_config() -> Dict[str, int]:
    """
    获取所有平台的并发限制配置
    Returns:
        Dict[str, int]: 平台标识到并发限制数的映射
    """
    config = load_config()
    platforms = config['platforms']
    
    return {
        platform_key: platform_info.get('concurrent', 1)
        for platform_key, platform_info in platforms.items()
    }