from typing import Optional, List, Dict
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.actions import Action
from agent.utils.common_util import is_json
from pydantic import Field, model_validator
from metagpt.utils.common import OutputParser
from agent.utils.tool_details import TOOL_DETEAIL
from metagpt.tools.search_engine import SearchEngine
from agent.prompts.prompt import KNOWLEDGE_BASE_SYSTEM_PROMPT, KNOWLEDGE_BASE_STEP_PROMPT, \
    INTENT_ANALYSIS_PROMPT, KEYWORDS_ANALYSIS_PROMPT, MATCH_TOOLS_PROMPT, FAULT_DIRECTORY_PROMPT, FAULT_CONTENTS_PROMPT

import re
import json
import pydantic

# 全局变量存储
global_intent_info = {}

# 关键字存储
global_instruction_keywords = ""


class AnalysisIntentAction(Action):
    """
    分析意图动作
    """
    name: str = 'AnalysisIntentAction'

    async def run(self, interaction: str):
        # 替换提示词指令
        prompt = INTENT_ANALYSIS_PROMPT.format(instruction=interaction, language="Chinese")

        # 请求大模型
        resp = await self._aask(prompt)

        # 格式化数据结果
        code_text = AnalysisIntentAction.parse_code(resp)

        # 赋值到全局变量
        if is_json(code_text):
            json_object = json.loads(code_text)
            global_intent_info['intent'] = json_object.get("intent")
        # 返回结果
        return code_text

    @staticmethod
    def parse_code(rsp):
        pattern = r"```python(.*)```"
        match = re.search(pattern, rsp, re.DOTALL)
        code_text = match.group(1) if match else rsp
        return code_text


class AnalysisKeywordAction(Action):
    """
    关键字提取动作
    """

    name: str = 'AnalysisKeywordAction'

    async def run(self, code_text: str):
        # 替换提示词指令
        prompt = KEYWORDS_ANALYSIS_PROMPT.format(instruction=code_text, language="Chinese")

        # 请求大模型
        resp = await self._aask(prompt)

        # 格式化数据结果
        code_text = AnalysisIntentAction.parse_code(resp)

        # 赋值到全局变量
        if is_json(code_text):
            json_object = json.loads(code_text)
            global_intent_info['keywords'] = json_object.get("keywords")

        # 返回结果
        return code_text


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

    async def run(self, context: list[Message], system_text=KNOWLEDGE_BASE_SYSTEM_PROMPT) -> str:
        if self.search_engine is None:
            logger.warning("配置SERI_PAPAPI_KEY、SERPER_API_KEY、GOOGLE_API_KEY之一以解锁全部功能")
            return ""

        query = context[-1].content
        # logger.debug(query)
        query_json = json.loads(query)
        global global_instruction_keywords
        global_instruction_keywords = "".join(query_json['keywords'])
        rsp = await self.search_engine.run(''.join(query_json['keywords']))
        self.result = rsp
        if not rsp:
            logger.error("empty rsp...")
            return ""
        # logger.info(rsp)

        system_prompt = [system_text]

        prompt = KNOWLEDGE_BASE_STEP_PROMPT.format(
            ROLE=self.prefix,
            CONTEXT=rsp,
            QUERY_HISTORY="\n".join([str(i) for i in context[:-1]]),
            QUERY=str(context[-1]),
        )
        result = await self._aask(prompt, system_prompt)
        logger.debug(prompt)
        logger.debug(f"知识库返回结果{result}")
        msg = Message(content=result, cause_by=type(self))
        return msg


class ToolAnalysisAction(Action):
    name: str = "ToolAnalysisAction"
    profile: str = "tool_analysis_action"
    code_nums: List = []
    result_report: List = []

    async def run(self, context: list[Message]):
        query = json.loads(context)
        self.code_nums = []
        # 循环步骤查询知识库相关知识
        for item in query['steps']:
            step_prompt = MATCH_TOOLS_PROMPT.format(language="Chinese", instruction=item,
                                                    tools=TOOL_DETEAIL)
            result = await self._aask(step_prompt)
            logger.info(f"工具调用结果：{result}")
            if is_json(result):
                result_json = json.loads(result)
                if result_json['code_num']:
                    if result_json['code_num'] in self.code_nums:
                        logger.info("已有该工具")
                    else:
                        self.code_nums.append(result_json['code_num'])
        return json.dumps(self.code_nums)


class ToolCallAction(Action):
    """
    工具调用角色
    """
    name: str = "ToolCallAction"
    profile: str = "tool_call_action"

    async def run(self, context: list[Message]):
        # return context

        result = [
            {
                "title": "日志检查工具处理结果",
                "content": """
                   1.2024年06-24 09:00:32条推信号和2024年06-24 09:00:34条推信号之间丢失一次堆叠信号。
                   2.2024年06-24 09:00:44条推信号和2024年06-24 09:00:46条推信号之间丢失一次堆叠信号。
                   3.2024年06-24 09:00:33出现1次full gc。   
                   4.2024年06-24 09:00:45出现1次full gc。
                   """
            },
            {
                "title": "配置文件校验工具处理结果",
                "content": """
                    1.边侧配置文件校验结果：正常
                    2.端侧配置文件校验结果：正常
                    3.算法配置文件校验结果：正常。
                    """
            },
            {
                "title": "数据库检查工具处理结果",
                "content": """
                    1.2024年06-24 09:00:32条推信号和2024年06-24 09:00:34条推信号之间丢失一次堆叠信号。
                    2.2024年06-24 09:00:44条推信号和2024年06-24 09:00:46条推信号之间丢失一次堆叠信号。 
                    """
            }
        ]

        return json.dumps(result)


class FaultDirectoryAction(Action):
    """Action class for writing tutorial directories.

    Args:
        name: The name of the action.
        language: The language to output, default is "Chinese".
    """

    name: str = "FaultDirectoryAction"
    language: str = "Chinese"

    async def run(self) -> Dict:
        """Execute the action to generate a tutorial directory according to the topic.
        Args:
            topic: The tutorial topic.
        Returns:
            the tutorial directory information, including {"title": "xxx", "directory": [{"dir 1": ["sub dir 1", "sub dir 2"]}]}.
        """
        global global_instruction_keywords
        prompt = FAULT_DIRECTORY_PROMPT.format(topic=global_instruction_keywords, language=self.language)
        resp = await self._aask(prompt=prompt)
        return OutputParser.extract_struct(resp, dict)


class FaultContentAction(Action):
    """Action class for writing tutorial content.

    Args:
        name: The name of the action.
        directory: The content to write.
        language: The language to output, default is "Chinese".
    """

    name: str = "FaultContentAction"
    directory: dict = dict()
    language: str = "Chinese"

    async def run(self, context:List[Message]) -> str:
        """Execute the action to write document content according to the directory and topic.

        Args:
            topic: The tutorial topic.

        Returns:
            The written tutorial content.
        """
        prompt = FAULT_CONTENTS_PROMPT.format(topic=context, language=self.language, directory=self.directory)
        return await self._aask(prompt=prompt)

