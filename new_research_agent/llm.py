import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()


# 所有 LLM 节点共享同一个基础模型配置。
model = ChatOpenAI(
    model=os.environ["LLM_MODEL_ID"],
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ["LLM_BASE_URL"],
    temperature=0,
    extra_body={
        "thinking": {
            "type": "disabled",
        }
    },
)