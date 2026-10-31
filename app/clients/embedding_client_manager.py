import asyncio
from typing import Optional

import os
import httpx
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.conf.app_config import app_config, EmbeddingConfig


class EmbeddingClientManager:
    def __init__(self,config:EmbeddingConfig):
        self.client:Optional[object] =None
        self.config =config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"
    def init(self):
        # Use DashScope's OpenAI-compatible Qwen embedding endpoint when an
        # Aliyun key is available; otherwise keep the course's local backend.
        if os.getenv("ALIYUN_API_KEY"):
            self.client = QwenEmbeddings(
                api_key=os.environ["ALIYUN_API_KEY"],
                model=os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3"),
                dimension=app_config.qdrant.embedding_size,
            )
        else:
            self.client = HuggingFaceEndpointEmbeddings(model=self._get_url())

embedding_manager = EmbeddingClientManager(app_config.embedding)


class QwenEmbeddings(Embeddings):
    def __init__(self, api_key: str, model: str, dimension: int):
        self.api_key, self.model, self.dimension = api_key, model, dimension
        self.url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        results = []
        async with httpx.AsyncClient(timeout=60) as client:
          for start in range(0, len(texts), 10):
            batch = texts[start:start + 10]
            response = await client.post(
                self.url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": {"texts": batch},
                      "parameters": {"dimension": self.dimension, "output_type": "dense"}},
            )
            if response.is_error:
                raise RuntimeError(f"Qwen embedding failed {response.status_code}: {response.text[:500]}")
            items = response.json()["output"]["embeddings"]
            results.extend(item["embedding"] for item in sorted(items, key=lambda x: x["text_index"]))
        return results

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("Use aembed_documents in this async project")

    def embed_query(self, text: str) -> list[float]:
        raise RuntimeError("Use aembed_query in this async project")

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return (await self._embed([text]))[0]

if __name__ == '__main__':
    # 初始化向量对象
    embedding_manager.init()
    # 获取向量对象
    embeddings=embedding_manager.client
    # 定义异步函数
    async def test():
        # 定义文本
        text="我是中国人"
        text_list=["我是中国人","我爱中国"]
        # 转换 list[float]
        # query_result =await embeddings.aembed_query(text)
        # list[list[float],list[float]]
        result_list=await embeddings.aembed_documents(text_list)

        print(result_list)
        # print(len(query_result))
        # print(type(query_result))
        # print(query_result)

    asyncio.run(test())









