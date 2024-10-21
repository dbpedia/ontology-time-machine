import argparse
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Type, TypeVar


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
    DEPENDENCY_MANIFEST = "dependencyManifest"


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
    logLevel: LogLevel = LogLevel.INFO
    ontoFormatConf: OntoFormatConfig = field(default_factory=OntoFormatConfig)
    ontoVersion: OntoVersion = OntoVersion.ORIGINAL_FAILOVER_LIVE_LATEST
    restrictedAccess: bool = False
    clientConfigViaProxyAuth: ClientConfigViaProxyAuth = ClientConfigViaProxyAuth.IGNORE
    httpsInterception: HttpsInterception = HttpsInterception.ALL
    disableRemovingRedirects: bool = False
    timestamp: str = ""
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


def parse_arguments(config_str: str = "") -> Config:
    default_cfg: Config = Config()
    parser = argparse.ArgumentParser(description="Process ontology format and version.")

    # Defining ontoFormat argument with nested options
    parser.add_argument(
        "--ontoFormat",
        type=lambda s: enum_parser(OntoFormat, s),
        default=default_cfg.ontoFormatConf.format,
        choices=list(OntoFormat),
        help="Format of the ontology: turtle, ntriples, rdfxml, htmldocu",
    )

    parser.add_argument(
        "--ontoPrecedence",
        type=lambda s: enum_parser(OntoPrecedence, s),
        default=default_cfg.ontoFormatConf.precedence,
        choices=list(OntoPrecedence),
        help="Precedence of the ontology: default, enforcedPriority, always",
    )

    parser.add_argument(
        "--patchAcceptUpstream",
        type=bool,
        default=default_cfg.ontoFormatConf.patchAcceptUpstream,
        help="Defines if the Accept Header is patched upstream in original mode.",
    )

    # Defining ontoVersion argument
    parser.add_argument(
        "--ontoVersion",
        type=lambda s: enum_parser(OntoVersion, s),
        default=default_cfg.ontoVersion,
        choices=list(OntoVersion),
        help="Version of the ontology: original, originalFailoverLive, originalFailoverArchivoMonitor, latestArchive, timestampArchive, dependencyManifest",
    )

    # Enable/disable mode to only proxy requests to ontologies
    parser.add_argument(
        "--restrictedAccess",
        type=bool,
        default=default_cfg.restrictedAccess,
        help="Enable/disable mode to only proxy requests to ontologies stored in Archivo.",
    )

    # Enable HTTPS interception for specific domains
    parser.add_argument(
        "--httpsInterception",
        type=lambda s: enum_parser(HttpsInterception, s),
        default=default_cfg.httpsInterception,
        choices=list(HttpsInterception),
        help="Enable HTTPS interception for specific domains: none, archivo, all, listfilename.",
    )

    # Enable/disable inspecting or removing redirects
    parser.add_argument(
        "--disableRemovingRedirects",
        type=bool,
        default=default_cfg.disableRemovingRedirects,
        help="Enable/disable inspecting or removing redirects.",
    )

    parser.add_argument(
        "--clientConfigViaProxyAuth",
        type=lambda s: enum_parser(ClientConfigViaProxyAuth, s),
        default=default_cfg.clientConfigViaProxyAuth,
        choices=list(ClientConfigViaProxyAuth),
        help="Define the configuration of the proxy via the proxy auth.",
    )

    # Log level
    parser.add_argument(
        "--logLevel",
        type=lambda s: enum_parser(LogLevel, s),
        default=default_cfg.logLevel,
        choices=list(LogLevel),
        help="Level of the logging: debug, info, warning, error.",
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
    #     logger.info(f"Manifest File Path: {args.manifest}")
    #     manifest = args.manifest
    # else:
    #     manifest = None

    # print the default configuration with all nested members
    # print(default_cfg)  # TODO remove

    # Initialize the Config class with parsed arguments
    config = Config(
        logLevel=args.logLevel,
        ontoFormatConf=OntoFormatConfig(
            args.ontoFormat, args.ontoPrecedence, args.patchAcceptUpstream
        ),
        ontoVersion=args.ontoVersion,
        restrictedAccess=args.restrictedAccess,
        httpsInterception=args.httpsInterception,
        clientConfigViaProxyAuth=args.clientConfigViaProxyAuth,
        disableRemovingRedirects=args.disableRemovingRedirects,
        timestamp=args.timestamp if hasattr(args, "timestamp") else "",
    )

    return config
