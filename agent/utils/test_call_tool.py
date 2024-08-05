import requests
# 测试调用日志工具
def test_call_log_util():
    return requests.get("http://127.0.0.1:9804/meta/gpt/test/util")
# 算法配置校验工具
def test_call_algorithm_conf_util(i:int):
    if i == 0:
        return """
            当前机器算法配置正确。
           """
    else:
        return """
            1.allTierNum不符合当前机器堆叠层数。
            2.pushNum不符合件推次数
           """
# 数据库调用工具
def test_call_database_util(i:int):
    if i == 0:
        return """
            数据库中没有异常信号。
           """
    else:
        return """
            1.2024-06-21 09:50:00 - 2024-06-21 09:52:00 2次条推中间缺失一次堆叠信号。
            2.2024-06-21 09:50:54丢失一次件推信号
           """
# 连接校验工具
def test_call_connect_util(i:int):
    if i == 0:
        return """
            数据库连接正常。
            读码器连接正常。
            PLC连接正常。
           """
    else:
        return """
            数据库连接正常。
            读码器连接4次请求，2次丢包。
            PLC连接4次请求，2次丢包。
           """

# 测试调用读码器工具
def test_call_camera_util(i:int):
    if i == 0:
        return """
                读码器配置正确。
               """
    else:
        return """
                读码器触发方式错误。
               """