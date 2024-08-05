import json

from metagpt.actions import Action
from metagpt.schema import Message

res_msg = []


class LogAction(Action):
    name:str = "LogAction"
    async def run(self, context: list[Message]):
        print(f"{self.name}收到消息{context}")
        log_check = {
            "title":"日志检查工具处理结果",
            "content":"""
            1.2024年06-24 09:00:32条推信号和2024年06-24 09:00:34条推信号之间丢失一次堆叠信号。
            2.2024年06-24 09:00:44条推信号和2024年06-24 09:00:46条推信号之间丢失一次堆叠信号。
            3.2024年06-24 09:00:33出现1次full gc。   
            4.2024年06-24 09:00:45出现1次full gc。
            """
        }
        global res_msg
        res_msg.append(log_check)
        return "日志检查工具处理完成"


class ConfigAction(Action):
    name: str = "ConfigAction"
    async def run(self, context: list[Message]):
        print(f"{self.name}收到消息{context}")
        config_check = {
            "title":"配置文件校验工具处理结果",
            "content":"""
            1.边侧配置文件校验结果：正常
            2.端侧配置文件校验结果：正常
            3.算法配置文件校验结果：正常。
            """
        }

        global res_msg

        res_msg.append(config_check)
        return "配置文件校验工具执行完成"


class DataBaseAction(Action):
    name: str = "DataBaseAction"
    async def run(self, context: list[Message]):
        print(f"{self.name}收到消息{context}")
        db_check = {
            "title":"数据库检查工具处理结果",
            "content":"""
            1.2024年06-24 09:00:32条推信号和2024年06-24 09:00:34条推信号之间丢失一次堆叠信号。
            2.2024年06-24 09:00:44条推信号和2024年06-24 09:00:46条推信号之间丢失一次堆叠信号。 
            """
        }
        global res_msg
        res_msg.append(db_check)
        return "数据库检查工具执行完成"


class ConnectAction(Action):
    name: str = "ConnectAction"
    async def run(self, context: list[Message]):
        print(f"{self.name}收到消息{context}")
        connect_check = {
            "title":"连接校验工具处理结果",
            "content":"""
            1.PLC连接正常
            2.所有读码器连接正常
            3.边侧连接正常
            """
        }
        global res_msg
        res_msg.append(connect_check)
        return "连接校验工具执行完成"



class CameraConfAction(Action):
    name: str = "CameraConfAction"
    async def run(self, context: list[Message]):
        print(f"{self.name}收到消息{context}")
        camera_check = {
            "title":"读码器配置文件校验工具处理结果",
            "content":"""
            1.条码校验工位-内测读码器发送数据格式正确
            2.读码器
            """
        }
        res_msg.append(camera_check)
        return "读码器配置文件校验工具执行完成"

class IntegrationResultAction(Action):
    name: str = "IntegrationResultAction"
    async def run(self, context: list[Message]):
        global res_msg

        return json.dumps(res_msg)