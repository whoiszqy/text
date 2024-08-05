from metagpt.roles.role import Role, RoleReactMode
from metagpt.rag.engines import SimpleEngine
from typing import Dict
from datetime import datetime
from metagpt.utils.file import File
from examples.rag_pipeline import EXAMPLE_DATA_PATH
from metagpt.const import DATA_PATH
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.tools.search_engine import SearchEngine
from agent_v2.problem_action import AnalysisIntentAction, AnalysisKeywordAction, RagAction, ToolAnalysisAction, \
    ToolCallAction, FaultDirectoryAction, FaultContentAction

import uuid

DOC_PATH = EXAMPLE_DATA_PATH / "ragTest/单通道问题处理方案.md"

action_ids = []



class ProblemHandleRole(Role):
    name: str = 'ProblemHandleRole'
    profile: str = "ProblemHandleRole"
    total_content: str = ""
    language:str="Chinese"
    directory:Dict = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        simple_store = SimpleEngine.from_docs(input_files=[DOC_PATH])
        search_store = SearchEngine.from_search_func(search_func=simple_store.asearch, proxy=self.config.proxy)
        rag_action = RagAction(search_engine=search_store, context=self.context)
        self.set_actions([
            AnalysisIntentAction,
            AnalysisKeywordAction,
            rag_action,
            ToolAnalysisAction,
            ToolCallAction,
            FaultDirectoryAction,
            FaultContentAction
        ])

        self._set_react_mode(RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        """Perform an action as determined by the role.

        Returns:
            A message containing the result of the action.
        """
        global action_ids
        todo = self.rc.todo
        if type(todo) is FaultDirectoryAction:
            msg = self.rc.memory.get(k=1)[0]
            self.topic = msg.content
            resp = await todo.run(self.topic)
            logger.info(resp)
            return await self._handle_directory(resp)
        if type(todo) is FaultContentAction:
            resp = await todo.run(self.directory)
        else:
            resp = await todo.run(self.rc.memory.get(k=1)[0])
        if type(todo) is FaultContentAction:
            if self.total_content != "":
                self.total_content += "\n\n\n"
            self.total_content += resp
        logger.info(resp)
        return Message(content=resp, role=self.profile)
    async def _handle_directory(self, titles: Dict) -> Message:
        """Handle the directories for the tutorial document.

        Args:
            titles: A dictionary containing the titles and directory structure,
                    such as {"title": "xxx", "directory": [{"dir 1": ["sub dir 1", "sub dir 2"]}]}

        Returns:
            A message containing information about the directory.
        """
        self.main_title = titles.get("title")
        # directory = f"{self.main_title}\n"
        self.total_content += f"# {self.main_title}"
        # actions.py = []
        # global action_ids
        # for first_dir in titles.get("directory"):
        #     action_id = str(uuid.uuid4())
        #     action_ids.append(action_id)
        #     # actions.py.append(FaultContentAction(language=self.language, directory=first_dir,id=action_id))
        #     key = list(first_dir.keys())[0]
        #     directory += f"- {key}\n"
        #     for second_dir in first_dir[key]:
        #         directory += f"  - {second_dir}\n"
        # self.set_actions(actions.py)
        # self.rc.max_react_loop = len(self.actions.py)
        self.directory = titles.get("directory")
        return Message()
    async def react(self) -> Message:
        msg = await super().react()
        root_path = DATA_PATH / "fault_analysis_doc" / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        await File.write(root_path, f"{self.main_title}.md", self.total_content.encode("utf-8"))
        msg.content = str(root_path / f"{self.main_title}.md")
        return msg