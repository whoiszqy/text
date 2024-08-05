import re

import fire
import pydantic
from pydantic import Field, model_validator
from typing import Optional
from metagpt.actions import Action, UserRequirement
from pydantic import BaseModel, ConfigDict, Field
from metagpt.logs import logger
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.environment import Environment
from metagpt.const import MESSAGE_ROUTE_TO_ALL
from metagpt.strategy.planner import Planner
from metagpt.schema import Message, Plan, Task, TaskResult
from agent_v1.problem_action import RagAction
from metagpt.actions.di.ask_review import AskReview, ReviewConst
from metagpt.tools.search_engine import SearchEngine
from agent_v1.prompt import KNOWLEDGE_BASE_SYSTEM_PROMPT, KNOWLEDGE_BASE_STEP_PROMPT

from metagpt.actions.di.write_plan import (
    WritePlan,
    precheck_update_plan_from_rsp,
    update_plan_from_rsp,
)

import asyncio

PROMPT = """
Please analyze the intention of {instruction} and return the options in {options}, requiring:
1. Return the number corresponding to the option, for example: A
2. Do not have redundant output, including concluding remarks.
3. Only one option can be returned, multiple options cannot be returned
"""

OPTIONS = """
A: Generate report
B: Problem consultation
C: Other
"""

PROMPT_A = """
# Report Writing Prompt

## Task
Write a report

## Requirements
1. Retrieve information about the roles related to the report from the knowledge base.
2. Strictly define the sequence of execution to ensure that each role's responsibilities and involvement times are precise.
3. Return the report content in strict JSON format, ensuring that each field has a clear definition and format, for example: `[{"order":1, "code":"00001", "description":"Detailed description"},{"order":2, "code":"00002", "description":"other"}]`, and all fields must be included in the returned JSON.
4. The output must be strictly in the specified language, Chinese.
5. Do not have redundant output, including concluding remarks.

## Steps
1. **Step 1**: Extract information about the roles related to the report from the knowledge base, including but not limited to report writers, reviewers, approvers, etc.
2. **Step 2**: Based on the extracted role information, strictly determine the sequence of report writing to ensure that each role is involved at the appropriate time, avoiding any confusion or omissions in the process.
"""

PROMPT_B = """
"""

PROMPT_C = """
"""

PROMPT_TEMPLATE: str = """
    # Context:
    {context}
    # Available Task Types:
    {task_type_desc}
    # Task:
    Based on the context, write a plan or modify an existing plan of what you should do to achieve the goal. A plan consists of one to {max_tasks} tasks.
    If you are modifying an existing plan, carefully follow the instruction, don't make unnecessary changes. Give the whole plan unless instructed to modify only one task of the plan.
    If you encounter errors on the current task, revise and output the current single task only.
    Output a list of jsons following the format:
    ```json
    [
        {{
            "task_id": str = "unique identifier for a task in plan, can be an ordinal",
            "dependent_task_ids": list[str] = "ids of tasks prerequisite to this task",
            "instruction": "what you should do in this task, one short phrase or sentence",
            "task_type": "type of this task, should be one of Available Task Types",
        }},
        ...
    ]
    ```
    """

env = Environment()


class TestAction(Action):

    async def run(self, context: Message):
        logger.info(f'TestAction run {context.content}')
        prompt = PROMPT.format(instruction=context.content, options=OPTIONS)
        resp = await self._aask(prompt)
        return resp


class AnalysisIntentRole(Role):
    name: str = "AnalysisIntentRole"
    profile: str = "AnalysisIntentRole"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([TestAction])

    async def _act(self) -> Message:
        todo = self.rc.todo

        msg = self.rc.memory.get(k=1)[0]  # use all memories as context

        code_text = await todo.run(msg)  # specify arguments
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        return msg


class TestPlanAction(Action):
    async def run(self, context: Message):
        logger.info(f'TestAction run {context.content}')
        resp = await self.plan_roles(context.content)
        return resp

    async def plan_roles(self, flag: str):
        if flag == 'A':
            prompt = PROMPT_A
        elif flag == 'B':
            prompt = PROMPT_B
        else:
            prompt = PROMPT_C
        resp = [
            {
                "order": 1,
                "code": "00001",
                "description": "报告撰写者"
            },
            {
                "order": 2,
                "code": "00002",
                "description": "初步审阅者"
            },
            {
                "order": 3,
                "code": "00003",
                "description": "详细审阅者"
            },
            {
                "order": 4,
                "code": "00004",
                "description": "最终审批者"
            }
        ]

        return resp


class TestPlanRole(Role):
    name: str = "TestPlanRole"
    profile: str = "TestPlanRole"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([TestPlanAction])

    async def _act(self) -> Message:
        todo = self.rc.todo

        msg = self.rc.memory.get(k=1)[0]  # use all memories as context

        code_text = await todo.run(msg)  # specify arguments
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        return msg


class PlanAction(Action):
    async def run(self, context: Message):
        logger.info(f'PlanAction run {context.content}')
        return "context.content"

class RagAction(Action):
    name: str = "RagAction"
    content: Optional[str] = None
    search_engine: SearchEngine = None
    result: str = ""
    keyword_res: str = ""

    # 初始化查询引擎
    @model_validator(mode="after")
    def validate_search_engine(self):
        if self.search_engine is None:
            try:
                config = self.config
                search_engine = SearchEngine.from_search_config(config.search, proxy=config.proxy)
            except pydantic.ValidationError:
                search_engine = None

            self.search_engine = search_engine
        return self

    async def run(self, context: list[Message], max_tasks,system_text=KNOWLEDGE_BASE_SYSTEM_PROMPT) -> str:
        if self.search_engine is None:
            logger.warning("配置SERI_PAPAPI_KEY、SERPER_API_KEY、GOOGLE_API_KEY之一以解锁全部功能")
            return ""
        global global_instruction_keywords
        # logger.info(rsp)

        system_prompt = [system_text]

        prompt = PROMPT_TEMPLATE.format(
            context="\n".join([str(ct) for ct in context]), max_tasks=max_tasks, task_type_desc=task_type_desc
        )
        result = await self._aask(prompt, system_prompt)
        logger.debug(f"知识库返回结果{result}")
        return result

class TestPlanner(Planner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def update_plan(self, goal: str = "", max_tasks: int = 3, max_retries: int = 3):
        if goal:
            self.plan = Plan(goal=goal)

        plan_confirmed = False
        while not plan_confirmed:
            context = self.get_useful_memories()
            rsp = await RagAction().run(context, max_tasks=max_tasks)
            self.working_memory.add(Message(content=rsp, role="assistant", cause_by=WritePlan))

            # precheck plan before asking reviews
            is_plan_valid, error = super().precheck_update_plan_from_rsp(rsp, self.plan)  # 传入 self.plan
            if not is_plan_valid and max_retries > 0:
                error_msg = f"The generated plan is not valid with error: {error}, try regenerating, remember to generate either the whole plan or the single changed task only"
                logger.warning(error_msg)
                self.working_memory.add(Message(content=error_msg, role="assistant", cause_by=WritePlan))
                max_retries -= 1
                continue

            _, plan_confirmed = await self.ask_review(trigger=ReviewConst.TASK_REVIEW_TRIGGER)

        super().update_plan_from_rsp(rsp=rsp, current_plan=self.plan)  # 传入 self.plan

        self.working_memory.clear()


class PlanRole(Role):
    name: str = "PlanRoleNew"
    profile: str = "PlanRoleNew"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([PlanAction])
        self._watch({TestAction})
        self._set_react_mode(RoleReactMode.PLAN_AND_ACT)

        self.planner = TestPlanner()

    async def _act(self, context: Message) -> Message:
        todo = self.rc.todo

        msg = self.rc.memory.get(k=1)[0]  # use all memories as context

        code_text = await todo.run(msg)  # specify arguments
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        return msg


async def main():
    env.add_roles([AnalysisIntentRole(), PlanRole()])
    env.publish_message(
        Message(content="故障分析报告", send_to=AnalysisIntentRole),
    )

    n_round = len(env.get_roles())

    while n_round > 0:
        n_round -= 1
        await env.run()
    return env.history


if __name__ == '__main__':
    asyncio.run(main())
