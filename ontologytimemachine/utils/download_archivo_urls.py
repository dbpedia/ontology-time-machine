import os
import hashlib
import logging
import requests
import schedule
import time
import csv
from datetime import datetime, timedelta
from urllib.parse import urlparse
from typing import Set, Tuple


ARCHIVO_PARSED_URLS: Set[Tuple[str, str]] = set()


ARCHIVO_FILE_PATH = "ontologytimemachine/utils/archivo_ontologies_download.txt"
ARCHIVO_URL = "https://databus.dbpedia.org/ontologies/archivo-indices/ontologies/2024.07.26-220000/ontologies_type=official.csv"
HASH_FILE_PATH = "ontologytimemachine/utils/archivo_ontologies_hash.txt"


LAST_DOWNLOAD_TIMESTAMP = None
DOWNLOAD_INTERVAL = timedelta(days=1)  # 1 day interval for checking the download


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def schedule_daily_download():
    """Schedule the download to run at 3 AM every day."""
    schedule.every().day.at("03:00").do(download_archivo_urls)

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute if there’s a scheduled task


# Start the scheduler in the background
def start_scheduler():
    logger.info("Starting the scheduler for daily archivo ontology download.")
    schedule_daily_download()


# Function to calculate hash of the downloaded file
def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


# Function to download and update archivo URLs file
def download_archivo_urls():
    """Download the archivo ontologies file, extract the first column, and save to a text file if a new version is available."""
    try:
        logger.info("Checking for new version of archivo ontologies")

        # Download the latest archivo ontologies CSV
        response = requests.get(ARCHIVO_URL)
        response.raise_for_status()  # Ensure the request was successful

        # Save the file temporarily to calculate the hash
        temp_file_path = "temp_ontology_indices.csv"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(response.content)

        # Calculate the hash of the new file
        new_file_hash = calculate_file_hash(temp_file_path)

        # Compare with the existing hash if available
        if os.path.exists(HASH_FILE_PATH):
            with open(HASH_FILE_PATH, "r") as hash_file:
                old_file_hash = hash_file.read().strip()
        else:
            old_file_hash = None

        if new_file_hash != old_file_hash:
            # New version detected, extract the first column and save to the text file
            with open(temp_file_path, "r", newline="", encoding="utf-8") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=",")
                with open(ARCHIVO_FILE_PATH, "w") as txt_file:
                    for row in csv_reader:
                        if row:
                            txt_file.write(
                                row[0].strip() + "\n"
                            )  # Write only the first column (URL) to the text file

            # Save the new hash
            with open(HASH_FILE_PATH, "w") as hash_file:
                hash_file.write(new_file_hash)

            logger.info("New version of archivo ontologies downloaded and saved.")
        else:
            # No new version, remove the temporary file
            os.remove(temp_file_path)
            logger.info("No new version of archivo ontologies detected.")

        # Update the last download timestamp
        global LAST_DOWNLOAD_TIMESTAMP
        LAST_DOWNLOAD_TIMESTAMP = datetime.now()

    except requests.RequestException as e:
        logger.error(f"Failed to download archivo ontologies: {e}")


def load_archivo_urls():
    """Load the archivo URLs into the global variable if not already loaded or if a day has passed since the last download."""
    global ARCHIVO_PARSED_URLS
    global LAST_DOWNLOAD_TIMESTAMP

    # Check if ARCHIVO_PARSED_URLS is empty or the last download was over a day ago
    if not ARCHIVO_PARSED_URLS or (
        LAST_DOWNLOAD_TIMESTAMP is None
        or datetime.now() - LAST_DOWNLOAD_TIMESTAMP > DOWNLOAD_INTERVAL
    ):
        logger.info(
            "ARCHIVO_PARSED_URLS is empty or more than a day has passed since the last download."
        )
        download_archivo_urls()

    # Load archivo URLs after downloading or if already present
    if not ARCHIVO_PARSED_URLS:  # Load only if the set is empty
        logger.info("Loading archivo ontologies from file")
        try:
            with open(ARCHIVO_FILE_PATH, "r") as file:
                ARCHIVO_PARSED_URLS = {
                    (urlparse(line.strip()).netloc, urlparse(line.strip()).path)
                    for line in file
                }
            logger.info(f"Loaded {len(ARCHIVO_PARSED_URLS)} ontology URLs.")

        except FileNotFoundError:
            logger.error("Archivo ontology file not found.")
        except Exception as e:
            logger.error(f"Error loading archivo ontology URLs: {e}")
