from datetime import datetime
from metagpt.logs import logger
from typing import Optional,Dict
from metagpt.schema import Message
from metagpt.utils.file import File
from metagpt.const import DATA_PATH
from pydantic import Field, model_validator
from metagpt.roles.role import Role, RoleReactMode
from metagpt.tools.search_engine import SearchEngine
from agent.actions.problem_handle_action import AnalysisIntentAction, AnalysisKeywordAction
from agent.actions.problem_handle_action import RagAction, ToolAnalysisAction, ToolCallAction, FaultDirectoryAction,FaultContentAction
from agent.actions.tool_action import LogAction, ConfigAction, ConnectAction, CameraConfAction, DataBaseAction, IntegrationResultAction

import json


class AnalysisRole(Role):
    """
    分析角色

    1.分析用户意图
    2.提出关键字
    """

    name: str = "AnalysisRole"
    profile: str = "AnalysisRole"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([AnalysisIntentAction, AnalysisKeywordAction])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo  # 执行AnalysisAction

        msg = self.get_memories(k=1)[0]  # 查找最新消息
        code_text = await todo.run(msg.content)

        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        if todo.name == 'AnalysisIntentAction':
            logger.info(f"意图返回的结果是{code_text}")
        else:
            logger.info(f"关键字返回的结果是{code_text}")
            self.rc.env.publish_message(msg)
        return msg


class RagRole(Role):
    """
    知识库调用角色
    """
    name: str = 'RagRole'
    profile: str = "RagRole"
    desc: str = (
        "As an industry problem-solving expert, my name is RagRole. I specialize in handling clients' inquiries."
        "expertise and precision. My responses are based solely on the information available in our knowledge"
        "In instances where your query extends beyond this scope, I'll honestly indicate my inability "
        "to provide an answer, rather than speculate or assume. Please note, each of my replies will be "
        "delivered with the professionalism and courtesy expected of a seasoned sales guide."
    )

    store: Optional[object] = Field(default=None, exclude=True)  # must inplement tools.SearchInterface

    @model_validator(mode="after")
    def validate_stroe(self):
        if self.store:
            search_engine = SearchEngine.from_search_func(search_func=self.store.asearch, proxy=self.config.proxy)
            action = RagAction(search_engine=search_engine, context=self.context)
        else:
            action = RagAction
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)
        self.set_actions([action])
        self._watch({AnalysisKeywordAction})
        return self


class ToolAnalysisRole(Role):
    """
    根据返回的步骤解析需要调用的工具
    返回工具编号
    """
    name: str = 'ToolAnalysisRole'
    profile: str = "ToolAnalysisRole"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)
        self.set_actions([ToolAnalysisAction])
        self._watch({RagAction})

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]
        code_text = await todo.run(msg.content)
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        return msg


class ToolCallRole(Role):
    name: str = "ToolCallRole"
    profile: str = "ToolCallRole"
    action_num: int = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._set_react_mode(react_mode=RoleReactMode.REACT.value)
        self.set_actions([ToolCallAction])
        self._watch({ToolAnalysisAction})

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0]
        code_text = await todo.run(msg.content)

        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        return msg

        if self.todo.name == "ToolCallAction":
            actions = []
            self._reset()

            todo = self.rc.todo

            msg = self.get_memories(k=1)[0]

            code_text = await todo.run(msg.content)

            code_nums = json.loads(code_text)
            for code_num in code_nums:
                if code_num == "00001":
                    actions.append(LogAction())
                elif code_num == "00002":
                    actions.append(ConfigAction())
                elif code_num == "00003":
                    actions.append(DataBaseAction())
                elif code_num == "00004":
                    actions.append(ConnectAction())
                elif code_num == "00005":
                    actions.append(CameraConfAction())
                else:
                    print("不在工具调用范围")
            if len(actions) > 0:
                self.set_actions(actions)
                self.action_num = len(actions)
            else:
                # 插入默认
                self.set_actions([])

        for action_item in self.actions:
            self.set_todo(action_item)
            todo = self.rc.todo
            msg = self.get_memories(k=1)[0]
            await todo.run(msg.content)
            self.action_num = self.action_num - 1
            super_self = self

            if self.action_num == 0:
                new_action = IntegrationResultAction()
                self.set_actions([new_action])
                super_self.set_todo(new_action)
                todo = self.rc.todo
                code_text = await todo.run(msg.content)

                default_action = ToolCallAction()
                self.set_actions([default_action])
                self.set_todo(default_action)

        res_msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        self.rc.env.publish_message(res_msg)

        return "工具分配执行完毕"

class FaultAnalysisRole(Role):
    """故障分析报告角色
    Args:
        name: 角色名称
        profile: 角色配置文件描述
        goal: 角色的目标
        constraints: 角色的约束或要求
        language: 生成文档的语言
    """
    name: str = 'FaultAnalysis'
    profile: str = 'Fault Analysis'
    goal: str = "Generate fault analysis report"
    constraints: str = "Strictly follow Markdown's syntax, with neat and standardized layout"
    language: str = "Chinese"

    topic: str = ""
    main_title: str = ""
    total_content: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([FaultDirectoryAction(language=self.language)])
        self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)
        self._watch({ToolCallAction})

    async def _handle_directory(self, titles: Dict) -> Message:
        """Handle the directories for the tutorial document.

        Args:
            titles: A dictionary containing the titles and directory structure,
                    such as {"title": "xxx", "directory": [{"dir 1": ["sub dir 1", "sub dir 2"]}]}

        Returns:
            A message containing information about the directory.
        """
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

    async def _act(self) -> Message:
        """Perform an action as determined by the role.

        Returns:
            A message containing the result of the action.
        """
        todo = self.rc.todo
        if type(todo) is FaultDirectoryAction:
            msg = self.rc.memory.get(k=1)[0]
            self.topic = msg.content
            resp = await todo.run(topic=self.topic)
            logger.info(resp)
            return await self._handle_directory(resp)
        resp = await todo.run(topic=self.topic)
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

class TestRole(Role):
    name: str = 'TestRole'
    profile : str = "TestRole"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._set_react_mode(react_mode=RoleReactMode.REACT.value)
        self._watch({ToolCallAction})

    async def _act(self) -> Message:
        print(self.rc.memory.get(k=1)[0])