import argparse
from dataclasses import dataclass, field
from enum import Enum
import logging
import os
from typing import Dict, Any, Type, TypeVar, List


# logging.basicConfig(
#     level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
# )
# logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#  '%(asctime)s - pid:%(process)d [%(levelname)-.1s] %(module)s.%(funcName)s:%(lineno)d - %(message)s'
    #   Logger.setup(args.log_file, args.log_level, args.log_format)

def _print_logger_info(context_info: str, logger: logging.Logger) -> None :
    print(context_info+" logger name:"+logger.name)
    print(context_info+" logger id:"+ str(id(logger)))
    print(context_info+" logger effictive Level:"+str(logger.getEffectiveLevel))
    print(context_info+" logger logLevel:"+str(logger.level))
    print(context_info+" logger parent:"+str(logger.parent))
    print(context_info+" logger handlers:"+str(logger.handlers))
    print(context_info+" logger parent handlers:"+str(logger.parent.handlers))

loggerpp = logging.getLogger(__name__)
#_print_logger_info("config.py getLogger(__name__)",loggerpp)
logger = logging.getLogger("ontologytimemachine.utils.config")
#_print_logger_info("config.py getLogger(ontologytimemachine.utils.config)",loggerpp)



class EnumValuePrint(
    Enum
):  # redefine how the enum is printed such that it will show up properly the cmd help message (choices)
    def __str__(self):
        return self.value


class LogLevel(EnumValuePrint):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class OntoFormat(EnumValuePrint):
    TURTLE = "turtle"
    NTRIPLES = "ntriples"
    RDFXML = "rdfxml"
    HTMLDOCU = "htmldocu"


class OntoPrecedence(EnumValuePrint):
    DEFAULT = "default"
    ENFORCED_PRIORITY = "enforcedPriority"
    ALWAYS = "always"


class OntoVersion(EnumValuePrint):
    ORIGINAL = "original"
    ORIGINAL_FAILOVER_LIVE_LATEST = "originalFailoverLiveLatest"
    LATEST_ARCHIVED = "latestArchived"
    TIMESTAMP_ARCHIVED = "timestampArchived"
    #DEPENDENCY_MANIFEST = "dependencyManifest"


class HttpsInterception(EnumValuePrint):
    NONE = "none"
    ALL = "all"
    BLOCK = "block"
    ARCHIVO = "archivo"


class ClientConfigViaProxyAuth(EnumValuePrint):
    IGNORE = "ignore"
    REQUIRED = "required"
    OPTIONAL = "optional"


@dataclass
class OntoFormatConfig:
    format: OntoFormat = OntoFormat.NTRIPLES
    precedence: OntoPrecedence = OntoPrecedence.ENFORCED_PRIORITY
    patchAcceptUpstream: bool = False


@dataclass
class Config:
    logLevelTimeMachine: LogLevel = LogLevel.DEBUG
    logLevelBase: LogLevel = LogLevel.INFO
    ontoFormatConf: OntoFormatConfig = field(default_factory=OntoFormatConfig)
    ontoVersion: OntoVersion = OntoVersion.LATEST_ARCHIVED
    restrictedAccess: bool = False
    clientConfigViaProxyAuth: ClientConfigViaProxyAuth = ClientConfigViaProxyAuth.IGNORE
    httpsInterception: HttpsInterception = HttpsInterception.ALL
    disableRemovingRedirects: bool = False
    timestamp: str = ""
    host: List[str] = field(default_factory=lambda: ["0.0.0.0", "::"])
    port: int = 8898
    # manifest: Dict[str, Any] = None


# Define a TypeVar for the enum class
E = TypeVar("E", bound=Enum)


def enum_parser(enum_class: Type[E], value: str) -> E:
    value_lower = value.lower()
    try:
        return next(e for e in enum_class if e.value.lower() == value_lower)
    except StopIteration as exc:
        valid_options = ", ".join([e.value for e in enum_class])
        raise argparse.ArgumentTypeError(
            f"Invalid value '{value}'. Available options are: {valid_options}"
        ) from exc

def log_level_Enum_to_python_logging(log_level: LogLevel) -> int:
    """
    Translates the custom LogLevel enum into logging module levels.
    
    Args:
        log_level (LogLevel): The log level from the custom enum.
    
    Returns:
        int: Corresponding logging module level.
    """
    level_mapping = {
        LogLevel.DEBUG: logging.DEBUG,
        LogLevel.INFO: logging.INFO,
        LogLevel.WARNING: logging.WARNING,
        LogLevel.ERROR: logging.ERROR,
        LogLevel.CRITICAL: logging.CRITICAL,
    }

    # Return the corresponding logging level, defaulting to WARNING if not found
    return level_mapping.get(log_level, logging.WARNING)



def parse_arguments(config_str: str = "") -> Config:
    default_cfg: Config = Config()
    parser = argparse.ArgumentParser(
        description="Ontology Time Machine Proxy powered by DBpedia Archivo",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    help_suffix_template = "(default: %(default)s)"

    # Defining ontoFormat argument with nested options
    parser.add_argument(
        "--ontoFormat",
        type=lambda s: enum_parser(OntoFormat, s),
        default=default_cfg.ontoFormatConf.format,
        choices=list(OntoFormat),
        help=f"Format of the ontology. {help_suffix_template}",
    )

    parser.add_argument(
        "--ontoPrecedence",
        type=lambda s: enum_parser(OntoPrecedence, s),
        default=default_cfg.ontoFormatConf.precedence,
        choices=list(OntoPrecedence),
        help=f"Precedence of the ontology. {help_suffix_template}",
    )

    parser.add_argument(
        "--patchAcceptUpstream",
        action="store_true",
        default=default_cfg.ontoFormatConf.patchAcceptUpstream,
        help=f"Defines if the Accept Header is patched upstream in original mode. {help_suffix_template}",
    )

    # Defining ontoVersion argument
    parser.add_argument(
        "--ontoVersion",
        type=lambda s: enum_parser(OntoVersion, s),
        default=default_cfg.ontoVersion,
        choices=list(OntoVersion),
        help=f"Version of the ontology. {help_suffix_template}",
    )

    # Enable/disable mode to only proxy requests to ontologies
    parser.add_argument(
        "--restrictedAccess",
        action="store_true",
        default=default_cfg.restrictedAccess,
        help=f"Enable/disable mode to only proxy requests to ontologies stored in Archivo. {help_suffix_template}",
    )

    # Enable HTTPS interception for specific domains
    parser.add_argument(
        "--httpsInterception",
        type=lambda s: enum_parser(HttpsInterception, s),
        default=default_cfg.httpsInterception,
        choices=list(HttpsInterception),
        help=f"Enable HTTPS interception for specific domains. {help_suffix_template}",
    )

    # Enable/disable inspecting or removing redirects
    parser.add_argument(
        "--disableRemovingRedirects",
        action="store_true",
        default=default_cfg.disableRemovingRedirects,
        help=f"Enable/disable inspecting or removing redirects. {help_suffix_template}",
    )

    parser.add_argument(
        "--clientConfigViaProxyAuth",
        type=lambda s: enum_parser(ClientConfigViaProxyAuth, s),
        default=default_cfg.clientConfigViaProxyAuth,
        choices=list(ClientConfigViaProxyAuth),
        help=f"Define the configuration of the proxy via the proxy auth. {help_suffix_template}",
    )

    # Log level
    parser.add_argument(
        "--logLevelTimeMachine",
        type=lambda s: enum_parser(LogLevel, s),
        default=default_cfg.logLevelTimeMachine,
        choices=list(LogLevel),
        help=f"Level of the logging. {help_suffix_template}",
    )

    # Log level
    parser.add_argument(
        "--logLevelBase",
        type=lambda s: enum_parser(LogLevel, s),
        default=default_cfg.logLevelTimeMachine,
        choices=list(LogLevel),
        help=f"Level of the logging. {help_suffix_template}",
    )

    # Host
    parser.add_argument(
        "--host",
        type=str,
        nargs='+',  # Accepts one or more hostnames
        default=default_cfg.host,
        help=f"Hostnames or IP addresses to bind the proxy to. Multiple hosts can be provided. {help_suffix_template}",
    )

    # Port
    parser.add_argument(
        "--port",
        type=int,
        default=default_cfg.port,
        help=f"Port number to bind the proxy to. {help_suffix_template}",
    )

    if config_str:
        args = parser.parse_args(config_str)
    else:
        args = parser.parse_args()

    # Check the value of --ontoVersion and prompt for additional arguments if needed
    if args.ontoVersion == "timestampArchived":
        args.timestamp = input("Please provide the timestamp (e.g., YYYY-MM-DD): ")
    # Commenting manifest related code as it is not supported in the current version
    # elif args.ontoVersion == 'dependencyManifest':
    #     args.manifest = input('Please provide the manifest file path: ')

    # Accessing the arguments
    if hasattr(args, "timestamp"):
        timestamp = args.timestamp
    else:
        timestamp = None

    # if hasattr(args, 'manifest'):
    #     logger.debug(f"Manifest File Path: {args.manifest}")
    #     manifest = args.manifest
    # else:
    #     manifest = None

    # print the default configuration with all nested members
    # print(default_cfg)  # TODO remove
    # self.logger.setLevel(LogLevel.DEBUG)
    
    
    logger2 = logger
    #set the log level of proxypy and other modules
    logging.basicConfig(
        level=log_level_Enum_to_python_logging(args.logLevelBase), format="%(asctime)s - |%(name)s| %(levelname)s - %(message)s"
    )

    #set the log level of the time machine independently  
    formatter = logging.Formatter("%(asctime)s ||| %(name)s ||| - %(levelname)s - %(message)s")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        if (not "PYTEST_CURRENT_TEST" in os.environ):
            logger.propagate = False # Prevent the logger from propagating to the root logger otherwise it will print the log messages twice
    else:
    # If handlers exist, apply the formatter to all handlers
        for handler in logger.handlers:
            handler.setFormatter(formatter)

    # global logger2 #global var seems to construct a logger object with another id which is weird seems to lead to issues with setting the log levels
    #logger2 = logging.getLogger("ontologytimemachine.utils.config")
    #_print_logger_info("before: config.py->parse_arguments getLogger(ontologytimemachine.utils.config)",logger2)

    if args.logLevelTimeMachine == LogLevel.DEBUG:
        logger.setLevel(log_level_Enum_to_python_logging(LogLevel.DEBUG))
        #_print_logger_info("after: config.py->parse_arguments getLogger(ontologytimemachine.utils.config)",logger2)
        logger.debug(f"Logging level set to: {args.logLevelTimeMachine}")
    elif args.logLevelTimeMachine == LogLevel.INFO:
        logger.setLevel(logging.INFO)
        logger.info(f"Logging level set to: {args.logLevelTimeMachine}")
    elif args.logLevelTimeMachine == LogLevel.WARNING:
        logger.setLevel(logging.WARNING)
        logger.warning(f"Logging level set to: {args.logLevelTimeMachine}")
    elif args.logLevelTimeMachine == LogLevel.ERROR:
        logger.setLevel(logging.ERROR)
        logger.error(f"Logging level set to: {args.logLevelTimeMachine}")
    elif args.logLevelTimeMachine == LogLevel.CRITICAL:
        logger.setLevel(logging.CRITICAL)
        logger.critical(f"Logging level set to: {args.logLevelTimeMachine}")

    # Initialize the Config class with parsed arguments
    config = Config(
        logLevelTimeMachine=args.logLevelTimeMachine,
        logLevelBase=args.logLevelBase,
        ontoFormatConf=OntoFormatConfig(
            args.ontoFormat, args.ontoPrecedence, args.patchAcceptUpstream
        ),
        ontoVersion=args.ontoVersion,
        restrictedAccess=args.restrictedAccess,
        httpsInterception=args.httpsInterception,
        clientConfigViaProxyAuth=args.clientConfigViaProxyAuth,
        disableRemovingRedirects=args.disableRemovingRedirects,
        timestamp=args.timestamp if hasattr(args, "timestamp") else "",
        host=args.host,
        port=args.port,
    )

    return config
