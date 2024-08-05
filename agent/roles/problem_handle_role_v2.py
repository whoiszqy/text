from datetime import datetime
from metagpt.logs import logger
from typing import Optional,Dict,List
from metagpt.schema import Message
from metagpt.utils.file import File
from metagpt.const import DATA_PATH
from pydantic import Field, model_validator
from metagpt.roles.role import Role, RoleReactMode
from examples.rag_pipeline import EXAMPLE_DATA_PATH
from metagpt.rag.engines import SimpleEngine
from metagpt.tools.search_engine import SearchEngine
from agent.actions.problem_handle_action import AnalysisIntentAction, AnalysisKeywordAction
from agent.actions.problem_handle_action import RagAction, ToolAnalysisAction, ToolCallAction, FaultDirectoryAction,FaultContentAction

DOC_PATH = EXAMPLE_DATA_PATH / "ragTest/单通道问题处理方案.md"

class ProblemHandleRole(Role):
    name: str = 'ProblemHandleRole'
    profile: str = "ProblemHandleRole"


    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        simple_store = SimpleEngine.from_docs(input_files=[DOC_PATH])
        search_store = SearchEngine.from_search_func(search_func=simple_store.asearch, proxy=self.config.proxy)
        rag_action = RagAction(search_engine=search_store,context=self.context)
        self.set_actions([
            AnalysisIntentAction,
            AnalysisKeywordAction,
            rag_action,
            ToolAnalysisAction,
            ToolCallAction,
            FaultDirectoryAction
        ])

        self._set_react_mode(RoleReactMode.BY_ORDER.value)
    async def _handle_directory(self, titles: Dict):
        self.main_title = titles.get("title")
        directory = f"{self.main_title}\n"
        self.total_content += f"# {self.main_title}"
        actions = list(self.actions)
        for first_dir in titles.get("directory"):
            actions.append(FaultContentAction(language=self.language, directory=first_dir))
            key = list(first_dir.keys())[0]
            directory += f"- {key}\n"
            for second_dir in first_dir[key]:
                directory += f"  - {second_dir}\n"
        self.set_actions(actions)
        self.rc.max_react_loop = len(self.actions)
        return Message()
    async def _act(self):
        todo = self.rc.todo
        msg = self.rc.memory.get(k=1)[0]
        if type(todo) is FaultDirectoryAction:
            msg = self.rc.memory.get(k=1)[0]
            self.topic = msg.content
            resp = await todo.run(topic=self.topic)
            logger.info(resp)
            return await self._handle_directory(resp)
        resp = await todo.run(msg)
        logger.info(resp)
        if self.total_content != "":
            self.total_content += "\n\n\n"
        self.total_content += resp
        return Message(content=resp, role=self.profile)
    async def react(self) -> Message:
        msg = await super().react()
        root_path = DATA_PATH / "fault_analysis_doc" / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        await File.write(root_path, f"{self.main_title}.md", self.total_content.encode("utf-8"))
        msg.content = str(root_path / f"{self.main_title}.md")
        return msg