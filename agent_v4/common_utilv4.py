import json
import random


def is_json(jsonStr:str):
    """
    判断字符串是否是JSON格式
    """
    try:
        json.loads(jsonStr)
    except ValueError as e:
        return False
    return True
# 随机返回0或1
def random_zero_or_one():
    return random.randint(0, 1)