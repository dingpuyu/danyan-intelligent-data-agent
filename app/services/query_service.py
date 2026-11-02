import json

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.state import DataAgentState
from app.services.query_intent import get_direct_answer
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class QueryService:
    def __init__(self,
                 embedding_client:HuggingFaceEndpointEmbeddings,
                 column_qdrant_repository:ColumnQdrantRepository,
                 metric_qdrant_repository:MetricQdrantRepository,
                 value_es_repository:ValueEsRepository,
                 meta_mysql_repository:MetaMysqlRepository,
                 dw_mysql_repository:DwMysqlRepository
                 ):
        self.embedding_client=embedding_client
        self.column_qdrant_repository=column_qdrant_repository
        self.metric_qdrant_repository=metric_qdrant_repository
        self.value_es_repository=value_es_repository
        self.meta_mysql_repository=meta_mysql_repository
        self.dw_mysql_repository=dw_mysql_repository
    async def query(self, query: str):
        direct_answer = get_direct_answer(query)
        if direct_answer:
            yield f"data: {json.dumps({'answer': direct_answer}, ensure_ascii=False)}\n\n"
            return
        # 创建状态对象
        state = DataAgentState(query=query)
        # 创建上下文对象
        runtime = DataAgentContext(
            embedding_client=self.embedding_client,
            column_qdrant_repository=self.column_qdrant_repository,
            metric_qdrant_repository=self.metric_qdrant_repository,
            value_es_repository=self.value_es_repository,
            meta_mysql_repository=self.meta_mysql_repository,
            dw_mysql_repository=self.dw_mysql_repository
        )

        try:
            # 执行图
            async  for chunk in graph.astream(input=state, context=runtime, stream_mode="custom"):
                yield f"data: {json.dumps(chunk,ensure_ascii=False,default=str)}  \n\n"
        except Exception as e:
            detail = str(e).strip() or f"{type(e).__name__}: 下游服务暂时不可用"
            yield f"data: {json.dumps({'error': detail}, ensure_ascii=False, default=str)}  \n\n"
