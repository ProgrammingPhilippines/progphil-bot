import os

import dotenv
import yaml


class BotConfig(object):
    prefix: str
    token: str

    def __init__(self, prefix: str, token: str):
        self.prefix = prefix
        self.token = token


class GuildInfo(object):
    staff_roles: list[int]
    dev_help_forum: int
    log_channel: int

    def __init__(self, staff_roles: list[int], dev_help_forum: int, log_channel: int):
        self.staff_roles = staff_roles
        self.dev_help_forum = dev_help_forum
        self.log_channel = log_channel


class Database(object):
    name: str
    host: str
    user: str
    password: str
    port: int

    def __init__(self, name: str, host: str, user: str, password: str, port: int):
        self.name = name
        self.host = host
        self.user = user
        self.password = password
        self.port = port


class API(object):
    api_ninja: str

    def __init__(self, api_ninja: str):
        self.api_ninja = api_ninja


class LoggerConfig(object):
    log_channel: int
    log_level: str

    def __init__(self, log_channel: int, log_level: str):
        self.log_channel = log_channel
        self.log_level = log_level


class Config(object):
    def __init__(self):
        dotenv.load_dotenv()
        yaml.SafeLoader.add_constructor("!ENV", _load_env)

        with open("../../config/config.yml") as config:
            self.config = yaml.safe_load(config)

    def bot(self) -> BotConfig:
        token = self.config["bot"]["token"]
        prefix = self.config["bot"]["prefix"]

        return BotConfig(prefix, token)

    def guild(self) -> GuildInfo:
        staff_roles = self.config["guild"]["staff_roles"]
        dev_help_forum = self.config["guild"]["dev_help_forum"]
        log_channel = self.config["guild"]["log_channel"]

        return GuildInfo(staff_roles, dev_help_forum, log_channel)

    def database(self) -> Database:
        name = self.config["database"]["name"]
        host = self.config["database"]["host"]
        user = self.config["database"]["user"]
        password = self.config["database"]["password"]
        port = self.config["database"]["port"] or "5432"

        return Database(name, host, user, password, int(port))

    def api(self) -> API:
        api_ninja = self.config["api"]["api_ninja"]
        return API(api_ninja)

    def logger(self) -> LoggerConfig:
        log_channel = self.config["logger"]["log_channel"]
        log_level = self.config["logger"]["log_level"]

        return LoggerConfig(log_channel, log_level)


# dotenv.load_dotenv()


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


# yaml.SafeLoader.add_constructor("!ENV", _load_env)
#
# with open("../../config/config.yml", "r") as CONFIG:
#     CONFIG = yaml.safe_load(CONFIG)
#
#
# class ConfigGen(type):
#     """A metaclass for accessing configuration by accessing
#     class attributes.
#
#     key specifies the YAML key.
#
#     Example:
#         # config.yml
#
#         bot: <--- key
#             prefix: "!"
#             token: !ENV "token"
#
#
#         # config.py
#
#         class BotConfig(metaclass=ConfigGen):
#             key = "bot"
#
#             prefix: str
#             token: str
#
#         # main.py
#
#         from config import BotConfig
#
#         class PPH(Bot):
#             super().init(
#             **kwargs,
#             command_prefix=BotConfig.prefix,
#             intents=intents
#         )
#
#         instance = PPH()
#
#         instance.run(BotConfig.token)
#     """
#
#     def __getattr__(cls, name: str):
#         """This method will get invoked in the child class
#         when you try to get an attribute from the child class
#         """
#         try:
#             name = name.lower()
#             return CONFIG[cls.key][name]
#         except KeyError:
#             print(
#                 f"\u001b[31mERROR\u001b[37m: \u001b[33m{name}\u001b[37m was not found in the config file. Did you set it up correctly?"
#             )
#
#
# # Dataclasses here
# class BotConfig(metaclass=ConfigGen):
#     key = "bot"
#     prefix: str
#     token: str
#
#
# class GuildInfo(metaclass=ConfigGen):
#     key = "guild"
#
#     staff_roles: list[int]
#     dev_help_forum: int
#     log_channel: int
#
#
# class Database(metaclass=ConfigGen):
#     key = "database"
#
#     name: str
#     host: str
#     user: str
#     password: str
#     port: str
#
#
# class API(metaclass=ConfigGen):
#     key = "api"
#
#     api_ninja: str
#
#
# class LoggerConfig(metaclass=ConfigGen):
#     key = "logger"
#
#     log_channel: int
#     log_level: str
