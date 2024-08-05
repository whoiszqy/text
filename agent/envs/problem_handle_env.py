"""
问题处理环境
"""
from metagpt.schema import Message
from metagpt.environment import Environment
from metagpt.rag.engines import SimpleEngine
from examples.rag_pipeline import EXAMPLE_DATA_PATH
from agent.roles.problem_handle_role import AnalysisRole,RagRole,ToolAnalysisRole,ToolCallRole,TestRole

DOC_PATH = EXAMPLE_DATA_PATH / "ragTest/单通道问题处理方案.md"

class ProblemHandleEnv:
    """
    问题处理环境
    """
    env: Environment() = None

    # 初始化
    def __init__(self):
        if self.env is None:
            self.env = Environment()
        know_store = SimpleEngine.from_docs(input_files=[DOC_PATH])
        self.env.add_roles([AnalysisRole(),RagRole(store=know_store),ToolAnalysisRole(),ToolCallRole(),TestRole()])
    async def _ask(self, message:str):
        self.env.publish_message(Message(content=message, send_to=AnalysisRole))

        for role in self.env.get_roles():
            print(f"角色{role}调用")

        # while not self.env.is_idle:
            await self.env.run()
        return {"code": 200, "msg": "报告已生成"}