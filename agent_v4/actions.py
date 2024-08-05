import json
import logging
import asyncio

from turtledemo.penrose import f
from typing import ClassVar, List, Any

import aiofiles
from pydantic import BaseModel
from nltk import choose
from openpyxl.styles.builtins import total

from typing import List, Optional

from rich import markdown

from agent_v4.common_utilv4 import is_json
from agent_v4.task_type import TaskType
from metagpt import context
from metagpt.logs import logger
from metagpt.actions.action import Action
from metagpt.schema import Message
from metagpt.utils.common import CodeParser
from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.rag.engines import SimpleEngine
from agent_v4.prompt import (ANALYSIS_INTENT_OPTIONS, ANALYSIS_INTENT_PROMPT, WRITE_PLAN_ACTION_PROMPT, SELECT_PROMPT,
                             PRODUCTION_RUN_PROMPT_V5, FAULT_DIRECTORY_PROMPT_V6, CONTENT_PROMPT1)
from metagpt.rag.schema import FAISSRetrieverConfig, FAISSIndexConfig

DOC_PATH = EXAMPLE_DATA_PATH / "ragTest/单通道问题处理任务规划.md"
PERSIST_DIR = EXAMPLE_DATA_PATH / "ragTest/tmp_storage"


class AnalysisIntentAction(Action):
    """
    分析意图
    """
    name: str = "AnalysisIntentAction"

    async def run(self, context: Message):
        logger.info(f'AnalysisIntentAction run {context.content}')
        prompt = ANALYSIS_INTENT_PROMPT.format(instruction=context.content, options=ANALYSIS_INTENT_OPTIONS)
        resp = await self._aask(prompt)
        return resp


class WritePlanTaskAction(Action):
    engine: SimpleEngine = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        retriever_configs = [FAISSRetrieverConfig()]
        SimpleEngine.from_docs(input_files=[DOC_PATH], retriever_configs=retriever_configs).persist(PERSIST_DIR)
        self.engine = SimpleEngine.from_index(index_config=FAISSIndexConfig(persist_path=PERSIST_DIR),
                                              retriever_configs=retriever_configs)

    async def run(self, context: Message, max_tasks):
        logger.info(f'WritePlanTaskAction run {context}')
        references = self.engine.query(context[0].content)
        task_type_desc = "\n".join([f"- **{tt.type_name}**: {tt.value.desc}" for tt in TaskType])
        prompt = WRITE_PLAN_ACTION_PROMPT.format(
            context="\n".join([str(ct) for ct in context]), max_tasks=max_tasks, task_type_desc=task_type_desc,
            references=references, language='Chinese'
        )
        rsp = await self._aask(prompt)
        rsp = CodeParser.parse_code(block=None, text=rsp)
        return rsp


class PlanTaskAction(Action):
    name: str = "PlanTask"

    async def run(self, context: Message):
        logger.info(f'PlanTaskAction run {context.content}')
        return context.content


class DirectoryPromptAction(Action):
    """
    目录生成提示词获取动作
    """
    name: str = "DirectoryPromptAction"

    async def run(self, context: Message):
        logger.info(f'DirectoryPromptAction run {context}')
        prompts = [{"PRODUCTION": PRODUCTION_RUN_PROMPT_V5}, {"FAULT": FAULT_DIRECTORY_PROMPT_V6}]
        prompt = SELECT_PROMPT.format(prompts=prompts,topic=context)
        resp = await self._aask(prompt)
        return resp


class DirectoryGenAction(Action):
    """
    目录生成动作
    """
    name: str = "DirectoryGenAction"

    async def run(self, context: Message):

        prompt_action = DirectoryPromptAction()
        prompt_result = await prompt_action.run(context)
        # Determine which prompt to use based on the result
        if "PRODUCTION" in prompt_result:
            prompt = PRODUCTION_RUN_PROMPT_V5.format(topic=context.content, language="Chinese")
        else:
            prompt = FAULT_DIRECTORY_PROMPT_V6.format(topic=context.content, language="Chinese")
        resp = await self._aask(prompt)
        logger.info(f'Director.yGenAction run {resp}')
        resp_format = CodeParser.parse_code(block=None, text=resp, lang="json")

        if is_json(resp_format):
            json_object = json.loads(resp_format)
        else:
            json_object = None
        return json.dumps(json_object)


class DirectoryContentFillingAction(Action):
    """
    目录内容填充
    """

    name: str = "DirectoryContentFilling"
    language: str = "Chinese"
    topic: str = "件烟关联生产运行分析"

    async def run(self, context: Message):
        # Generate the directory using DirectoryGenAction
        directory_gen_action = DirectoryGenAction()
        directory_result = await directory_gen_action.run(context)

        # Ensure directory_result is properly formatted JSON
        if is_json(directory_result):
            directory = json.loads(directory_result)
        else:
            directory = None

        # Use the directory in the prompt
        if directory:
            directory_str = json.dumps(directory,
                                       ensure_ascii=False)  # Use ensure_ascii=False to keep Chinese characters
            prompt = CONTENT_PROMPT1.format(topic=self.topic, language=self.language, directory=directory_str)
        else:
            # Handle the case where directory is None or not valid JSON
            prompt = CONTENT_PROMPT1.format(topic=self.topic, language=self.language, directory="{}")

        # Ask the prompt and get the response
        resp = await self._aask(prompt)
        logger.info(f'DirectoryContentFillingAction run {resp}')

        # Convert the response to Markdown format
        md_content = self.convert_to_markdown(resp)

        # Save the result to a Markdown file
        self.save_to_markdown(md_content, 'directory_content4.md')

        return resp

    def convert_to_markdown(self, content):
        """
        Convert the JSON response to Markdown format.
        """
        try:
            data = json.loads(content)
            md_lines = []
            if "title" in data and "directory" in data:
                md_lines.append(f"# {data['title']}")
                self.format_directory(md_lines, data['directory'])
            return "\n".join(md_lines)
        except json.JSONDecodeError:
            return content

    def format_directory(self, md_lines, directory, level=1):
        """
        Recursively format the directory structure into Markdown.
        """
        for item in directory:
            for dir_name, sub_dirs in item.items():
                md_lines.append(f"{'#' * level} {dir_name}")
                if isinstance(sub_dirs, list):
                    self.format_directory(md_lines, sub_dirs, level + 1)

    def save_to_markdown(self, content, filename):
        """
        Save the content to a Markdown file.
        """
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)






class StepAnalysisAction(Action):
    """
    步骤生成动作
    """
    name: str = "StepAnalysisAction"

    async def run(self, context: Message):
        logger.info(f'DirectoryGenAction run {context.content}')
        return context.content


class SummarizeAction(Action):
    """
    总结动作
    """
    name: str = "SummarizeAction"

    async def run(self, context: Message):
        logger.info(f'DirectoryGenAction run {context.content}')
        return context.content


class DocumentGenerationAction(Action):
    """
    Document Generation Action
    """
    name: str = "DocumentGenerationAction"
    directory: dict = dict()
    language: str = "Chinese"

    async def run(self, context: Message):
        logger.info(f'DocumentGenerationAction run with context: {context.content}')
        # Assuming there's a function or method to generate the document based on the context
        # document_text = generate_document(context.content)
        prompt_action = DirectoryGenAction()
        prompt_result = await prompt_action.run(context)
        if "" in prompt_result:
            prompt = CONTENT_PROMPT1.format(topic=context.content, language=self.language, directory=self.directory)
        return await self._aask(prompt=prompt)


class OtherAction(Action):
    async def run(self, prompt: str):
        logger.info(f'DirectoryGenAction run {prompt}')
        result = await self._aask(prompt)
        return result
