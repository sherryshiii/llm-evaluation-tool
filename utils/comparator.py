COMPARE_FUNCTIONS = {
    "compare_text": "字符串比较",
    "compare_json": "JSON比较",
    "compare_region": "地区比较",
    "compare_complex_json": "多层级JSON比较"
}

def compare_text(text1: str, text2: str) -> bool:
    """
    比较两个字符串是否相同，忽略首尾空白字符，大小写不敏感
    
    Args:
        text1: 第一个字符串
        text2: 第二个字符串
        
    Returns:
        bool: 如果字符串相同则返回True，否则返回False
    """
    if text1 is None and text2 is None:
        return True
    
    if text1 is None or text2 is None:
        return False
    
    # 转换为字符串并处理
    text1 = str(text1).strip().lower()
    text2 = str(text2).strip().lower()
    
    return text1 == text2

def compare_json(text1: str, text2: str) -> bool:
    """
    比较两个JSON字符串的key/value是否一致
    
    Args:
        text1: 第一个JSON字符串
        text2: 第二个JSON字符串
        
    Returns:
        bool: 如果JSON相同则返回True，否则返回False
    """
    import json
    
    try:
        dict1 = json.loads(text1) if text1 else {}
        dict2 = json.loads(text2) if text2 else {}
    except:
        # 如果解析失败，则作为普通字符串比较
        return compare_text(text1, text2)
    
    # 如果任一解析结果为空，且两者不同时为空，则返回False
    if (not dict1 and dict2) or (dict1 and not dict2):
        return False
    
    # 如果两者都为空，则返回True
    if not dict1 and not dict2:
        return True
    
    # 获取所有键
    keys = set(dict1.keys()) | set(dict2.keys())
    
    # 比较所有键值对
    for key in keys:
        # 检查键是否存在于两个字典中
        if key not in dict1 and key not in dict2:
            continue
        
        if key not in dict1 or key not in dict2:
            return False
        
        # 获取值并进行比较
        value1 = dict1[key]
        value2 = dict2[key]
        
        # 如果值是字符串，则忽略首尾空白字符进行比较
        if isinstance(value1, str) and isinstance(value2, str):
            if value1.strip() != value2.strip():
                return False
        # 否则直接比较
        elif value1 != value2:
            return False
    
    return True

def compare_region(text1: str, text2: str) -> bool:
    """
    比较两个地区JSON字符串是否匹配，包括省市区和街道信息
    
    Args:
        text1: 第一个地区JSON字符串
        text2: 第二个地区JSON字符串
        
    Returns:
        bool: 如果地区信息匹配则返回True，否则返回False
    """
    import json
    
    try:
        dict1 = json.loads(text1) if text1 else {}
        dict2 = json.loads(text2) if text2 else {}
    except:
        # 如果解析失败，则作为普通字符串比较
        return compare_text(text1, text2)
    
    # 如果任一解析结果为空，且两者不同时为空，则返回False
    if (not dict1 and dict2) or (dict1 and not dict2):
        return False
    
    # 如果两者都为空，则返回True
    if not dict1 and not dict2:
        return True
    
    # 比较省市区字段
    for field in ["province", "city", "district"]:
        expected_value = dict2.get(field, "").strip()
        actual_value = dict1.get(field, "").strip()
        if expected_value != actual_value:
            return False
    
    # 比较详细地址信息
    possible_address_fields = ["street", "address"]
    dict1_address = dict1.get(possible_address_fields[0], dict1.get(possible_address_fields[1], ""))
    dict2_address = dict2.get(possible_address_fields[0], dict2.get(possible_address_fields[1], ""))
    if dict1_address != dict2_address:
        return False

    return True

def compare_arrays(array1, array2) -> bool:
    """
    比较两个二维数组是否匹配
    只要array1中的每个元素在array2中都能找到对应的匹配项即可
    
    Args:
        array1: 第一个数组
        array2: 第二个数组
        
    Returns:
        bool: 如果数组匹配则返回True，否则返回False
    """
    if not isinstance(array1, list) or not isinstance(array2, list):
        return False
        
    for item1 in array1:
        if not isinstance(item1, dict):
            return item1 in array2
            
        item_matched = False
        for item2 in array2:
            if not isinstance(item2, dict):
                continue
                
            if all(item1.get(k, "").strip() == item2.get(k, "").strip() for k in item1.keys()):
                item_matched = True
                break
        if not item_matched:
            return False
    return True

def compare_complex_json(text1: str, text2: str) -> bool:
    """
    比较两个复杂JSON字符串是否匹配
    - 如果字段值是数组：支持多条记录匹配，只要有对应的记录完全匹配即可
    - 其他字段：进行精确匹配
    - 字段缺失：如果一边有字段而另一边没有，返回False
    
    Args:
        text1: 第一个复杂JSON字符串
        text2: 第二个复杂JSON字符串
        
    Returns:
        bool: 如果信息匹配则返回True，否则返回False
    """
    import json
    
    try:
        dict1 = json.loads(text1) if text1 else {}
        dict2 = json.loads(text2) if text2 else {}
    except:
        return compare_text(text1, text2)
    
    if (not dict1 and dict2) or (dict1 and not dict2):
        return False
    
    if not dict1 and not dict2:
        return True
    
    # 比较所有字段
    all_keys = set(dict1.keys()) | set(dict2.keys())
    for key in all_keys:
        # 检查字段是否存在
        exists1 = key in dict1
        exists2 = key in dict2
        
        # 如果字段在一边存在而另一边不存在，返回False
        if exists1 != exists2:
            return False
            
        value1 = dict1.get(key)
        value2 = dict2.get(key)
        
        # 如果是数组字段，使用数组比较逻辑
        if isinstance(value1, list) or isinstance(value2, list):
            # 确保两边都是数组
            if not isinstance(value1, list):
                value1 = [value1] if value1 is not None else []
            if not isinstance(value2, list):
                value2 = [value2] if value2 is not None else []
                
            if not compare_arrays(value1, value2):
                return False
        # 否则进行普通比较
        elif str(value1).strip() != str(value2).strip():
            return False
    
    return True
