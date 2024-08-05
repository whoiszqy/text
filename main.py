from fastapi import FastAPI
import uvicorn
from metagpt.logs import logger
from agent_v4.env import AgentEnvironment
from metagpt.schema import Message

app = FastAPI()

env = AgentEnvironment()

# problem_handle_env = ProblemHandleEnv()

@app.get("/meta/gpt/prompt")
async def say_hello(prompt: str):
    return await prompt_test(prompt)

@app.get("/meta/gpt/test/util")
async def say_test_util():
    return """
            1. 2024-06-21 09:52:34 出现一次Full GC。
            2. 2024-06-21 09:50:00 - 2024-06-21 09:52:00 缺失一次堆叠信号。
        """



async def prompt_test(msg):
    logger.info(msg)
    role_info = env.get_roles().get("AnalysisIntentRole")
    env.publish_message(Message(content=msg,send_to=role_info))
    while not env.is_idle:  # env.is_idle要等到所有Agent都没有任何新消息要处理后才会为True
        await env.run()
    return env.history


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=9804)
