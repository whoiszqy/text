from agent_v2.prompt import INTENT_ANALYSIS_PROMPT,KEYWORDS_ANALYSIS_PROMPT
from metagpt.actions import Action
from agent_v2.common_util import is_json
from typing import Optional, List, Dict
from metagpt.tools.search_engine import SearchEngine
from pydantic import Field, model_validator
from metagpt.schema import Message
from metagpt.logs import logger
from agent_v2.tool_details import TOOL_DETEAIL
from metagpt.utils.common import OutputParser
from agent_v2.tool_util_details import call_tool_by_condition

from agent_v2.prompt import KNOWLEDGE_BASE_SYSTEM_PROMPT, KNOWLEDGE_BASE_STEP_PROMPT, \
    INTENT_ANALYSIS_PROMPT, KEYWORDS_ANALYSIS_PROMPT, MATCH_TOOLS_PROMPT, FAULT_DIRECTORY_PROMPT, FAULT_CONTENTS_PROMPT,FAULT_DIRECTORY_PROMPT_V1,FAULT_CONTENT_COMMON_PROMPT_V1

import json
import re
import pydantic

global_intent_info = {}
global_instruction_keywords:str = ""

class AnalysisIntentAction(Action):
    """
    分析意图动作
    """
    name: str = 'AnalysisIntentAction'

    async def run(self, instruction: str):
        # 替换提示词指令
        prompt = INTENT_ANALYSIS_PROMPT.format(instruction=instruction, language="Chinese")

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

    async def run(self, instruction: str):
        # 替换提示词指令
        prompt = KEYWORDS_ANALYSIS_PROMPT.format(instruction=instruction, language="Chinese")

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

    async def run(self, instruction: list[Message], system_text=KNOWLEDGE_BASE_SYSTEM_PROMPT) -> str:
        if self.search_engine is None:
            logger.warning("配置SERI_PAPAPI_KEY、SERPER_API_KEY、GOOGLE_API_KEY之一以解锁全部功能")
            return ""
        # logger.debug(query)
        keyword_list = global_intent_info['keywords']
        global global_instruction_keywords
        global_instruction_keywords = "".join(keyword_list)
        rsp = await self.search_engine.run(''.join(keyword_list))
        self.result = rsp
        if not rsp:
            logger.error("empty rsp...")
            return ""
        # logger.info(rsp)

        system_prompt = [system_text]

        prompt = KNOWLEDGE_BASE_STEP_PROMPT.format(
            ROLE=self.prefix,
            CONTEXT=rsp,
            QUERY=str(global_instruction_keywords),
        )
        result = await self._aask(prompt, system_prompt)
        if is_json(result):
            json_object = json.loads(result)
            global_intent_info['steps'] = json_object.get("steps")
        logger.debug(prompt)
        logger.debug(f"知识库返回结果{result}")
        return result

class ToolAnalysisAction(Action):
    name: str = "ToolAnalysisAction"
    profile: str = "tool_analysis_action"
    code_nums: List = []
    result_report: List = []

    async def run(self, context: str):
        global global_intent_info
        query = global_intent_info["steps"]
        self.code_nums = []
        # 循环步骤查询知识库相关知识
        for item in query:
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
        global_intent_info['code_nums'] = self.code_nums
        return json.dumps(self.code_nums)

class ToolCallAction(Action):
    """
    工具调用角色
    """
    name: str = "ToolCallAction"
    profile: str = "tool_call_action"

    async def run(self, context:str):
        # return context
        global global_intent_info
        query = global_intent_info['code_nums']
        result = []
        for item in query:
            tool_call_res = call_tool_by_condition(item)
            if not type(tool_call_res) is str:
                result.append(tool_call_res)

        global_intent_info['tool_result'] = result
        json_res = json.dumps(result,ensure_ascii=False)
        return json_res


class FaultDirectoryAction(Action):
    """Action class for writing tutorial directories.

    Args:
        name: The name of the action.
        language: The language to output, default is "Chinese".
    """

    name: str = "FaultDirectoryAction"
    language: str = "Chinese"

    async def run(self,instruction:str) -> Dict:
        """Execute the action to generate a tutorial directory according to the topic.
        Args:
            topic: The tutorial topic.
        Returns:
            the tutorial directory information, including {"title": "xxx", "directory": [{"dir 1": ["sub dir 1", "sub dir 2"]}]}.
        """
        global global_instruction_keywords
        global global_intent_info
        tool_results = global_intent_info['tool_result']
        prompt = FAULT_DIRECTORY_PROMPT_V1.format(topic=global_instruction_keywords, language=self.language,tool_results=tool_results)
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
    id:str = ""
    total_content:str = ""

    async def run(self, context:List[Message]) -> str:
        """Execute the action to write document content according to the directory and topic.

        Args:
            topic: The tutorial topic.

        Returns:
            The written tutorial content.
        """
        global global_instruction_keywords
        for first_dir in context:
            global global_intent_info
            tool_results = global_intent_info['tool_result']
            prompt = FAULT_CONTENT_COMMON_PROMPT_V1.format(topic=global_instruction_keywords, language=self.language, directory=first_dir, tool_results=tool_results)
            content_res =  await self._aask(prompt=prompt)
            if self.total_content != "":
                self.total_content += "\n\n\n"
            self.total_content += content_res
        return self.total_content