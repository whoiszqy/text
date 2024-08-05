from metagpt.roles.role import Role, RoleReactMode
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message

import asyncio

class TestAction1(Action):
    name: str = "ToolAnalysisAction"

    async def run(self, context: str):
        logger.info(f"{str}------------1")


class TestAction2(Action):
    async def run(self, context: str):
        logger.info(f"{str}------------2")

class TestPlanAndAct(Role):
    name:str = 'TestPlanAndAct'
    profile:str = 'TestPlanAndAct'


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_actions([
            TestAction1,
            TestAction2,
        ])

        self._set_react_mode(RoleReactMode.PLAN_AND_ACT.value)

    async def _act(self) -> Message:
        msg = self.rc.memory.get(k=1)[0]
        todo = self.rc.todo
        resp = await todo.run(msg)
        return resp

    async def plan_and_act(self) -> Message:
        print("进来了")

if __name__ == '__main__':
    role = TestPlanAndAct()
    asyncio.run(role.run("故障分析"))