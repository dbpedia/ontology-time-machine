import os
import requests
import json
from urllib.parse import urlparse

def ensure_directory(path):
    """Ensure the directory exists."""
    if not os.path.exists(path):
        os.makedirs(path)

def save_file(content, file_path):
    """Save content to a file."""
    with open(file_path, "wb") as file:
        file.write(content)

def read_ontologies_from_file(file_path):
    """Read ontology URLs from a file where each line is an ontology URL."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    with open(file_path, "r") as file:
        return [line.strip() for line in file if line.strip()]

def download_ontology(url, formats, base_folder):
    """Download an ontology in specified formats and log details."""
    ontology_info = {
        "url": url,
        "downloads": {},
    }

    headers = {
        "Accept": "",
    }

    for format_name, mime_type in formats.items():
        try:
            headers["Accept"] = mime_type
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                parsed_url = urlparse(url)
                ontology_name = os.path.basename(parsed_url.path) or "ontology"
                ontology_url = url.replace('/', '_').replace(':', '_').replace('.', '_')
                filename = f"{ontology_url}.{format_name}"
                folder_path = os.path.join(base_folder, format_name)
                ensure_directory(folder_path)
                file_path = os.path.join(folder_path, filename)

                save_file(response.content, file_path)

                ontology_info["downloads"][format_name] = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "file_path": file_path,
                }
            else:
                ontology_info["downloads"][format_name] = {
                    "status_code": response.status_code,
                    "error": "Failed to fetch the ontology",
                }

        except Exception as e:
            ontology_info["downloads"][format_name] = {
                "error": str(e),
            }

    return ontology_info

def main():
    ontology_file = "archivo_ontologies.txt"
    urls = read_ontologies_from_file(ontology_file)

    formats = {
        "ttl": "text/turtle",
        "nt": "application/n-triples",
        "rdfxml": "application/rdf+xml",
    }

    base_folder = "downloads"
    ensure_directory(base_folder)

    log = []

    for url in urls:
        print(f'URL: {url}')
        ontology_log = download_ontology(url, formats, base_folder)
        log.append(ontology_log)

    log_file = os.path.join(base_folder, "download_log.json")
    with open(log_file, "w") as file:
        json.dump(log, file, indent=4)

    print(f"Download complete. Log saved to {log_file}")

if __name__ == "__main__":
    main()
