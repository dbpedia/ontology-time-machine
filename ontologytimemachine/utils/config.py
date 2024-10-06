import argparse
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Config:
    logLevel: LogLevel = LogLevel.INFO
    ontoFormat: Dict[str, Any] = None
    ontoVersion: str = ""
    restrictedAccess: bool = False
    httpsInterception: bool = False
    disableRemovingRedirects: bool = False
    timestamp: str = ""
    # manifest: Dict[str, Any] = None


def parse_arguments() -> Config:
    parser = argparse.ArgumentParser(description="Process ontology format and version.")

    # Defining ontoFormat argument with nested options
    parser.add_argument(
        "--ontoFormat",
        type=str,
        choices=["turtle", "ntriples", "rdfxml", "htmldocu"],
        default="turtle",
        help="Format of the ontology: turtle, ntriples, rdfxml, htmldocu",
    )

    parser.add_argument(
        "--ontoPrecedence",
        type=str,
        choices=["default", "enforcedPriority", "always"],
        default="enforcedPriority",
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
        type=str,
        choices=[
            "original",
            "originalFailoverLiveLatest",
            "latestArchived",
            "timestampArchived",
            "dependencyManifest",
        ],
        default="originalFailoverLiveLatest",
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
        type=str,
        choices=["none", "all", "block"],
        default="all",
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
        type=str,
        default="info",
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
        timestamp=timestamp,
        # manifest=manifest
    )

    return config
