import os

import dotenv
import yaml
from pydantic import BaseModel
import json


class BotConfig(BaseModel):
    prefix: str
    token: str


class GuildInfo(BaseModel):
    staff_roles: list[int]
    dev_help_forum: int
    log_channel: int


class Database(BaseModel):
    name: str
    host: str
    user: str
    password: str
    port: int


class API(BaseModel):
    api_ninja: str


class LoggerConfig(BaseModel):
    log_channel: int
    log_level: str


class Config(BaseModel):
    bot: BotConfig
    database: Database
    logger: LoggerConfig
    api: API
    guild: GuildInfo


def get_config(path: str) -> Config:
    dotenv.load_dotenv()
    yaml.SafeLoader.add_constructor("!ENV", _load_env)

    with open(path) as config:
        yaml_config = yaml.safe_load(config)
        bot_cfg = Config.model_validate_json(json.dumps(yaml_config))

        return bot_cfg


def _load_env(loader: yaml.Loader, node: yaml.ScalarNode) -> str:
    """A constructor for loading ENV YAML tags

    Usage in the YAML config:

        # Key is the config key
        app:
            key: !ENV "value"
    """

    default = None
    config_value = loader.construct_scalar(node)
    return os.getenv(config_value, default)
