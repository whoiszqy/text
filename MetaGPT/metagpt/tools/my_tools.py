from metagpt.tools.tool_recommend import ToolRecommender
from metagpt.schema import Plan
from metagpt.logs import logger
import numpy as np
from metagpt.tools.tool_data_type import Tool

class LogToolRecommender(ToolRecommender):
    """
    日志检验处理工具
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    async def recall_tools(self, context: str = "", plan: Plan = None, topk: int = 20) -> list[Tool]:
        query = plan.current_task.instruction if plan else context

        print(f"日志处理工具收到数据{query}")

        return query

class AlgorithmConfigToolRecommender(ToolRecommender):
    """
    算法配置检验处理工具
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    async def recall_tools(self, context: str = "", plan: Plan = None, topk: int = 20) -> list[Tool]:
        query = plan.current_task.instruction if plan else context

        print(f"算法配置检验处理工具收到数据{query}")

        return query

class DatabaseToolRecommender(ToolRecommender):
    """
    数据查询工具
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    async def recall_tools(self, context: str = "", plan: Plan = None, topk: int = 20) -> list[Tool]:
        query = plan.current_task.instruction if plan else context

        print(f"数据查询工具收到数据{query}")

        return query