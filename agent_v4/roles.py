from metagpt.rag.engines import SimpleEngine
from metagpt.roles.role import Role, RoleReactMode
from agent_v4.actions import AnalysisIntentAction, PlanTaskAction, WritePlanTaskAction, DirectoryPromptAction, \
    DirectoryGenAction, DocumentGenerationAction, StepAnalysisAction, SummarizeAction, OtherAction, \
    DirectoryContentFillingAction

from metagpt.logs import logger
from metagpt.schema import Message, Plan, Task, TaskResult
from metagpt.strategy.planner import Planner
from metagpt.actions.di.ask_review import ReviewConst
from metagpt.tools.tool_recommend import BM25ToolRecommender, ToolRecommender
from metagpt.tools.my_tools import LogToolRecommender, AlgorithmConfigToolRecommender, DatabaseToolRecommender
from metagpt.actions.di.execute_nb_code import ExecuteNbCode
from pydantic import Field, model_validator
from typing import Literal, List, Dict
from metagpt.utils.common import remove_comments
from metagpt.strategy.task_type import TaskType
from metagpt.utils.common import role_raise_decorator
from metagpt.actions.add_requirement import UserRequirement

import json

PLAN_STATUS = """
### Task
{task}
### Role List
{roles}
### Task guidance
Please return the name of the specified role based on the 'task' and meet the following requirements:
1. Strictly return in the specified language. {language}
2. Strictly return in dictionary form, for example: {{"roles": ["DirectoryGenRole","StepAnalysis Role"]}}.
3. There should be no extra spaces or line breaks.
"""


from metagpt.actions.di.write_plan import (
    WritePlan,
    precheck_update_plan_from_rsp,
    update_plan_from_rsp,
)


class IndustryPlanner(Planner):
    plan_action: WritePlanTaskAction = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plan_action = WritePlanTaskAction()
    async def update_plan(self, goal: str = "", max_tasks: int = 3, max_retries: int = 3):
        if goal:
            self.plan = Plan(goal=goal)

        plan_confirmed = False
        while not plan_confirmed:
            context = self.get_useful_memories()
            rsp = await self.plan_action.run(context, max_tasks=max_tasks)
            self.working_memory.add(Message(content=rsp, role="assistant", cause_by=WritePlan))

            # precheck plan before asking reviews
            is_plan_valid, error = precheck_update_plan_from_rsp(rsp, self.plan)
            if not is_plan_valid and max_retries > 0:
                error_msg = f"The generated plan is not valid with error: {error}, try regenerating, remember to generate either the whole plan or the single changed task only"
                logger.warning(error_msg)
                self.working_memory.add(Message(content=error_msg, role="assistant", cause_by=WritePlan))
                max_retries -= 1
                continue

            # _, plan_confirmed = await self.ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)
            # _ = 'confirm'
            plan_confirmed = True

        update_plan_from_rsp(rsp=rsp, current_plan=self.plan)

        self.working_memory.clear()

    async def process_task_result(self, task_result: TaskResult):
        # ask for acceptance, users can other refuse and change tasks in the plan
        # review, task_result_confirmed = await self.ask_review(task_result)
        review: str = 'confirm'
        task_result_confirmed: bool = True
        if task_result_confirmed:
            # tick off this task and record progress
            await self.confirm_task(self.current_task, task_result, review)

        elif "redo" in review:
            # Ask the Role to redo this task with help of review feedback,
            # useful when the code run is successful but the procedure or result is not what we want
            pass  # simply pass, not confirming the result

        else:
            # update plan according to user's feedback and to take on changed tasks
            await self.update_plan()

class AnalysisIntentRole(Role):
    name: str = "AnalysisIntentRole"
    profile: str = "AnalysisIntentRole"
    topic: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([AnalysisIntentAction])
        self._set_react_mode(RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.rc.memory.get(k=1)[0]
        self.rc.env.topic = msg.content
        # use all memories as context
        code_text = await todo.run(msg)  # specify arguments
        role_info = self.rc.env.roles.get('PlanRole')
        msg = Message(content=code_text, send_to=role_info)
        return msg
    def get_topic(self):
        return self.topic
    def set_topic(self, topic):
        self.topic = topic

class PlanRole(Role):
    """
    Planning role with enhanced interaction capabilities
    """
    name: str = "PlanRole"
    profile: str = "PlanRole"
    auto_run: bool = True
    use_plan: bool = True
    use_reflection: bool = False
    execute_code: ExecuteNbCode = Field(default_factory=ExecuteNbCode, exclude=True)
    tools: list[str] = []
    tool_recommenders: List[ToolRecommender] = Field(default_factory=list)
    react_mode: Literal["plan_and_act", "react"] = RoleReactMode.PLAN_AND_ACT.value
    max_react_loop: int = 10
    other_action: OtherAction = Field(default_factory=OtherAction)
    count_number: int = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([PlanTaskAction])
        self._set_react_mode(self.react_mode)
        self.planner = IndustryPlanner()
        self.tool_recommenders = [
            LogToolRecommender(),
            AlgorithmConfigToolRecommender(),
            DatabaseToolRecommender()
        ]

    @property
    def working_memory(self):
        return self.rc.working_memory
    async def _act_on_task(self, current_task: Task) -> TaskResult:
        # 收到任务之后执行任务
        code, result, is_success = await self.run_task()
        # 反馈结果
        return TaskResult(code=code, result=result, is_success=is_success)
    async def run_task(self, max_retry = 3):
        """
        @param: max_retry 重试次数，默认为3
        执行任务
        """
        counter = 0
        code = ""
        result = ""
        success = False
        roles_desc = []
        for role in self.rc.env.roles:
            if role != 'AnalysisIntentRole' and role != 'PlanRole':
                roles_desc.append({role:self.rc.env.roles.get(role).desc})
        # 1.获取任务匹配提示词
        prompt = PLAN_STATUS.format(task=self.planner.current_task.instruction, roles=roles_desc, language="Chinese")
        # 2.访问大模型，解析结果判断任务需要调用哪些角色
        role_res = await self.other_action.run(prompt=prompt)
        # 3.将信息循环推送给推荐的角色
        roles_json = json.loads(role_res)
        for role_name in roles_json['roles']:
            # 获取环境中的匹配的角色并推送数据
            role_info = self.rc.env.roles.get(role_name)
            self.rc.env.publish_message(Message(send_to=role_info))
            success = True
        # 4.判断任务是否执行完成
        return code,result,success

    @role_raise_decorator
    async def run(self, with_message=None) -> Message | None:
        """Observe, and think and act based on the results of the observation"""
        if with_message:
            msg = None
            if isinstance(with_message, str):
                msg = Message(content=with_message)
            elif isinstance(with_message, Message):
                msg = with_message
            elif isinstance(with_message, list):
                msg = Message(content="\n".join(with_message))
            if not msg.cause_by:
                msg.cause_by = UserRequirement
            self.put_message(msg)
        if not await self._observe():
            # If there is no new information, suspend and wait
            logger.debug(f"{self._setting}: no news. waiting.")
            return

        rsp = await self.react()

        # Reset the next action to be taken.
        self.set_todo(None)
        # Send the response message to the Environment object to have it relay the message to the subscribers.
        # self.publish_message(rsp)
        return rsp

    async def _get_tool_info(self):
        if not self.tool_recommenders:
            return ""
        context = self.working_memory.get()[-1].content if self.working_memory.get() else ""
        plan = self.planner.plan if self.use_plan else None
        tool_infos = []
        for recommender in self.tool_recommenders:
            tool_infos.append(await recommender.get_recommended_tool_info(context=context, plan=plan))
        return "\n".join(tool_infos)

class DirectoryGenRole(Role):
    """
    Directory Generation Role
    """
    name: str = "DirectoryGenRole"
    profile: str = "DirectoryGenRole"
    desc: str = "This role is responsible for generating directory structures based on the given context. It uses the most recent memory as context and generates the directory code text by executing the relevant action."
    menus_info: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([DirectoryPromptAction,DirectoryGenAction,DirectoryContentFillingAction])
        self._set_react_mode(RoleReactMode.BY_ORDER.value)

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.rc.memory.storage[0]  # use all memories as context
        code_text = await todo.run(msg)  # specify arguments
        topic = self.rc.env.get_topic()
        self.menus_info = code_text
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        return msg


class StepAnalysisRole(Role):
    """
    Step Analysis Role
    """
    name: str = "StepAnalysisRole"
    profile: str = "StepAnalysisRole"
    desc: str = "This role is designed to analyze and break down complex tasks into executable steps. It utilizes the most recent memory as context and obtains detailed steps by executing the relevant action."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([StepAnalysisAction])

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.rc.memory.storage[0]    # use the most recent memory as context
        msg = self.rc.memory.get(k=1)[0]    # use the most recent memory as context
        code_text = await todo.run(msg)  # specify arguments
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        return msg

class SummarizeRole(Role):
    """
    总结报告角色
    """
    name: str = "SummarizeRole"
    profile: str = "SummarizeRole"
    desc: str = "This role is responsible for generating concise summaries of complex information or lengthy reports. It utilizes the most recent memory as context to create a refined version of the content, facilitating quick understanding and review by executing the relevant action."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SummarizeAction])

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.rc.memory.storage[0]   # 使用所有记忆作为上下文
        code_text = await todo.run(msg)  # 指定参数
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        return msg

class DocumentGenerationRole(Role):
    """
    Document Generation Role
    """
    name: str = "DocumentGenerationRole"
    profile: str = "DocumentGenerationRole"
    desc: str = "This role is designed to generate comprehensive documents based on provided data and templates. It uses the most recent memory as context to create structured and formatted documents by executing the relevant action."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([DocumentGenerationAction])

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.rc.memory.storage[0]   # use the most recent memory as context
        document_text = await todo.run(msg)  # specify arguments
        msg = Message(content=document_text, role=self.profile, cause_by=type(todo))
        return msg