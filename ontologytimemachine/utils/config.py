import argparse
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class OntoFormat(Enum):
    TURTLE = "turtle"
    NTRIPLES = "ntriples"
    RDFXML = "rdfxml"
    HTMLDOCU = "htmldocu"


class OntoPrecedence(Enum):
    DEFAULT = "default"
    ENFORCED_PRIORITY = "enforcedPriority"
    ALWAYS = "always"


class OntoVersion(Enum):
    ORIGINAL = "original"
    ORIGINAL_FAILOVER_LIVE_LATEST = "originalFailoverLiveLatest"
    LATEST_ARCHIVED = "latestArchived"
    TIMESTAMP_ARCHIVED = "timestampArchived"
    DEPENDENCY_MANIFEST = "dependencyManifest"


class HttpsInterception(Enum):
    NONE = "none"
    ALL = "all"
    BLOCK = "block"
    ARCHIVO = "archivo"


@dataclass
class Config:
    logLevel: LogLevel = LogLevel.INFO
    ontoFormat: Dict[str, Any] = None
    ontoVersion: OntoVersion = (OntoVersion.ORIGINAL_FAILOVER_LIVE_LATEST,)
    restrictedAccess: bool = False
    httpsInterception: HttpsInterception = (HttpsInterception.ALL,)
    disableRemovingRedirects: bool = False
    timestamp: str = ""
    # manifest: Dict[str, Any] = None


def enum_parser(enum_class, value):
    value_lower = value.lower()
    try:
        return next(e.value for e in enum_class if e.value.lower() == value_lower)
    except StopIteration:
        valid_options = ", ".join([e.value for e in enum_class])
        raise ValueError(
            f"Invalid value '{value}'. Available options are: {valid_options}"
        )


def parse_arguments() -> Config:
    parser = argparse.ArgumentParser(description="Process ontology format and version.")

    # Defining ontoFormat argument with nested options
    parser.add_argument(
        "--ontoFormat",
        type=lambda s: enum_parser(OntoFormat, s),
        default=OntoFormat.TURTLE.value,
        help="Format of the ontology: turtle, ntriples, rdfxml, htmldocu",
    )

    parser.add_argument(
        "--ontoPrecedence",
        type=lambda s: enum_parser(OntoPrecedence, s),
        default=OntoPrecedence.ENFORCED_PRIORITY.value,
        help="Precedence of the ontology: default, enforcedPriority, always",
    )

    parser.add_argument(
        "--patchAcceptUpstream",
        type=bool,
        default=False,
        help="Defines if the Accept Header is patched upstream in original mode.",
    )

    # Defining ontoVersion argument
    parser.add_argument(
        "--ontoVersion",
        type=lambda s: enum_parser(OntoVersion, s),
        default=OntoVersion.ORIGINAL_FAILOVER_LIVE_LATEST.value,
        help="Version of the ontology: original, originalFailoverLive, originalFailoverArchivoMonitor, latestArchive, timestampArchive, dependencyManifest",
    )

    # Enable/disable mode to only proxy requests to ontologies
    parser.add_argument(
        "--restrictedAccess",
        type=bool,
        default=False,
        help="Enable/disable mode to only proxy requests to ontologies stored in Archivo.",
    )

    # Enable HTTPS interception for specific domains
    parser.add_argument(
        "--httpsInterception",
        type=lambda s: enum_parser(HttpsInterception, s),
        default=HttpsInterception.ALL.value,
        help="Enable HTTPS interception for specific domains: none, archivo, all, listfilename.",
    )

    # Enable/disable inspecting or removing redirects
    parser.add_argument(
        "--disableRemovingRedirects",
        type=bool,
        default=False,
        help="Enable/disable inspecting or removing redirects.",
    )

    # Log level
    parser.add_argument(
        "--logLevel",
        type=lambda s: enum_parser(LogLevel, s),
        default=LogLevel.INFO.value,
        help="Level of the logging: debug, info, warning, error.",
    )

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

    # Create ontoFormat dictionary
    ontoFormat = {
        "format": args.ontoFormat,
        "precedence": args.ontoPrecedence,
        "patchAcceptUpstream": args.patchAcceptUpstream,
    }

    # Initialize the Config class with parsed arguments
    config = Config(
        logLevel=args.logLevel,
        ontoFormat=ontoFormat,
        ontoVersion=args.ontoVersion,
        restrictedAccess=args.restrictedAccess,
        httpsInterception=args.httpsInterception,
        disableRemovingRedirects=args.disableRemovingRedirects,
        timestamp=args.timestamp if hasattr(args, "timestamp") else "",
    )

    return config
