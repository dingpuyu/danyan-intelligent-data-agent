from dataclasses import dataclass
from pathlib import Path
import os

from omegaconf import OmegaConf


# 日志配置
@dataclass
class File:
    enable: bool
    level: str
    path: str
    rotation: str
    retention: str


@dataclass
class Console:
    enable: bool
    level: str


@dataclass
class LoggingConfig:
    file: File
    console: Console


# 数据库配置
@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int


@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str


@dataclass
class ESConfig:
    host: str
    port: int
    index_name: str


@dataclass
class LLMConfig:
    model_name: str
    api_key: str


@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    llm: LLMConfig


config_file = Path(__file__).parents[2] / 'conf' / 'app_config.yaml'
context = OmegaConf.load(config_file)
schema = OmegaConf.structured(AppConfig)
app_config: AppConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))
# Prefer the runtime environment over the course's example credential.
# This keeps the checked-in course configuration reusable and avoids embedding
# a personal key in source files.
if os.getenv("DEEPSEEK_API_KEY"):
    app_config.llm.api_key = os.environ["DEEPSEEK_API_KEY"]

# Allow an existing local Docker volume to keep its own database credentials
# while clean installations use the sanitized defaults from app_config.yaml.
for prefix, db_config in (("DW_DB", app_config.db_dw), ("META_DB", app_config.db_meta)):
    if os.getenv(f"{prefix}_USER"):
        db_config.user = os.environ[f"{prefix}_USER"]
    if os.getenv(f"{prefix}_PASSWORD"):
        db_config.password = os.environ[f"{prefix}_PASSWORD"]
