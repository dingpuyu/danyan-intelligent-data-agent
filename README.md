# 青竹峰大衍智能问数 Agent

这是青竹峰科技大衍智能问数项目的脱敏学习版，用于学习和面试演示。用户输入业务问题，系统从元数据目录中检索表、字段、指标和字段取值，生成受控的 MySQL 查询 SQL，校验后返回结果。

## 技术栈

- FastAPI + SSE
- LangGraph Workflow Agent
- DeepSeek Chat
- Qwen `text-embedding-v3`
- MySQL 8
- Elasticsearch 8 + IK
- Qdrant
- SQLAlchemy Async + asyncmy

## 快速启动

```bash
cp .env.example .env
# 编辑 .env，填入模型 Key
set -a
source .env
set +a

docker-compose -f docker/docker-compose.yaml up -d mysql elasticsearch qdrant
./.venv/bin/python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml
./.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

打开 <http://127.0.0.1:8000/docs>，调用 `POST /api/query`：

```json
{"query":"统计华东地区销售额最高的三个商品"}
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

运行基础回归集：

```bash
./.venv/bin/python evals/run_eval.py --limit 5
```

## 目录

- `app/agent`：LangGraph 状态、上下文和工作流节点
- `app/api`：FastAPI 路由和请求模型
- `app/clients`：MySQL、ES、Qdrant、Embedding 客户端
- `app/repositories`：外部存储访问封装
- `app/services`：查询服务和元数据构建服务
- `conf/meta_config.yaml`：表、字段、指标目录配置
- `docker/mysql`：业务库和元数据库初始化脚本
- `prompts`：模型提示词
- `evals/questions.json`：基础评测问题集
- `docs/项目Wiki.md`：完整项目学习和面试 Wiki
- `docs/生产级问数架构与实现方案.md`：生产架构、实现路线和上线方案

## Embedding 说明

公开仓库不包含本地模型权重。设置 `ALIYUN_API_KEY` 后，项目会使用 DashScope 的 Qwen Embedding；没有该环境变量时才会回退到课程自带的本地 embedding 服务。

## 安全说明

不要把真实 API Key 写进 YAML、代码、日志或提交记录。生产环境还应增加只读数据库账号、SQL AST 白名单、权限过滤和查询超时。

当前版本已经在 EXPLAIN 和真实执行前增加只读 SQL 闸门，SQL 修正后会重新校验，连续失败达到上限后安全结束。
