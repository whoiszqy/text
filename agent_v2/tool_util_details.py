import json

def log_action(context: list):
    log_check = {
        "title": "日志检查工具处理结果",
        "content": """
        1.2024年06-24 09:00:32条推信号和2024年06-24 09:00:34条推信号之间丢失一次堆叠信号。
        2.2024年06-24 09:00:44条推信号和2024年06-24 09:00:46条推信号之间丢失一次堆叠信号。
        3.2024年06-24 09:00:33出现1次full gc。   
        4.2024年06-24 09:00:45出现1次full gc。
        """
    }
    return log_check

def config_action(context: list):
    config_check = {
        "title": "配置文件校验工具处理结果",
        "content": """
        1.边侧配置文件校验结果：正常
        2.端侧配置文件校验结果：正常
        3.算法配置文件校验结果：正常。
        """
    }
    return config_check

def database_action(context: list):
    db_check = {
        "title": "数据库检查工具处理结果",
        "content": """
        1.2024年06-24 09:00:32条推信号和2024年06-24 09:00:34条推信号之间丢失一次堆叠信号。
        2.2024年06-24 09:00:44条推信号和2024年06-24 09:00:46条推信号之间丢失一次堆叠信号。 
        """
    }
    return db_check

def connect_action(context: list):
    connect_check = {
        "title": "连接校验工具处理结果",
        "content": """
        1.PLC连接正常
        2.所有读码器连接正常
        3.边侧连接正常
        """
    }
    return connect_check

def camera_conf_action(context: list):
    camera_check = {
        "title": "读码器配置文件校验工具处理结果",
        "content": """
        1.条码校验工位-内测读码器发送数据格式正确
        2.读码器
        """
    }
    return camera_check
def call_tool_by_condition(condition: str):
    tools = {
        "00001": log_action,
        "00002": config_action,
        "00003": database_action,
        "00004": connect_action,
        "00005": camera_conf_action
    }
    if condition in tools:
        tool_func = tools[condition]
        tool_res_msg = tool_func([])  # 假设context为空列表
        return tool_res_msg
    else:
        return "00000"