import os
import requests
import json
import traceback
import time
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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

def get_causal_chain(exception):
    """Get the causal chain of exceptions."""
    chain = []
    while exception:
        chain.append({
            "type": type(exception).__name__,
            "message": str(exception),
        })
        exception = exception.__context__
    return chain

def get_type_chain(chain):
    """Get the type chain as a string separated by '||'."""
    return ' || '.join([entry['type'] for entry in chain])

def get_more_specific_type(chain):
    """Get the more specific type from the causal chain."""
    if len(chain) > 1:
        if chain[1]['type'] == 'MaxRetryError' and len(chain) > 2:
            return chain[2]['type']
        return chain[1]['type']
    return None

def download_ontology(url, formats, base_folder):
    """Download an ontology in specified formats and log details."""
    ontology_info = {
        "url": url,
        "downloads": {},
    }

    headers = {
        "Accept": "",
    }
    
    proxies = {
            "http": f"http://localhost:8898",
            "https": f"https://localhost:8898",
        }

    session = requests.Session()
    session.max_redirects = 10
    retries = Retry(total=0, backoff_factor=1, status_forcelist=[427]) # wanted to use for 429 originally, but backoff is als applied to connection timeouts and such
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    for format_name, mime_type in formats.items():
        print(f'Format name: {format_name}')
        try:
            headers["Accept"] = mime_type
            start_time = time.time()
            print(headers)
            response = session.get(url, headers=headers, proxies=proxies, timeout=10)
            print(response.content)
            request_duration = time.time() - start_time

            file_path = ""
            if response.status_code == 200:
                parsed_url = urlparse(url)
                ontology_name = os.path.basename(parsed_url.path) or "ontology"
                ontology_url = url.replace('/', '_').replace(':', '_').replace('.', '_')
                filename = f"{ontology_url}.{format_name}"
                folder_path = os.path.join(base_folder, format_name)
                ensure_directory(folder_path)
                file_path = os.path.join(folder_path, filename)

                download_start_time = time.time()
                save_file(response.content, file_path)
                download_duration = time.time() - download_start_time

            ontology_info["downloads"][format_name] = {
                "status_code": response.status_code,
                "file_path": file_path,
                "request_start_time": start_time,
                "request_duration": request_duration,
                "error": {
                    "type": None,
                    "type_more_specific": None,
                    "type_chain": None,
                    "message": None,
                    "traceback": None,
                    "chain_details": None,
                },
                "content_length": response.headers.get('Content-Length'),
                "content_lenght_measured": len(response.content),
                "content_type": response.headers.get('Content-Type'),
                "headers": dict(response.headers),
                # "download_duration": download_duration,
            }
            # else:
            #     ontology_info["downloads"][format_name] = {
            #         "status_code": response.status_code,
            #         "headers": dict(response.headers),
            #         "error": "Failed to fetch the ontology",
            #         "request_start_time": start_time,
            #         "request_duration": request_duration,
            #     }

        except Exception as e:
            request_duration = time.time() - start_time
            chain_details = get_causal_chain(e)
            ontology_info["downloads"][format_name] = {
                "status_code": None,
                "file_path": None,
                "request_start_time": start_time,
                "request_duration": request_duration,
                "content_length": None,
                "content_lenght_measured": None,
                "content_type": None,
                "error": {
                    "type": type(e).__name__,
                    "type_more_specific": get_more_specific_type(chain_details),
                    "type_chain": get_type_chain(chain_details),
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                    "chain_details": chain_details,
                },
                "headers": None
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

    base_folder = "downloads_proxy"
    ensure_directory(base_folder)

    log = []

    for url in urls:
        print(f'URL: {url}')
        ontology_log = download_ontology(url, formats, base_folder)
        time.sleep(0.2)
        log.append(ontology_log)

    log_file = os.path.join(base_folder, "download_proxy_log.json")
    with open(log_file, "w") as file:
        json.dump(log, file, indent=4)

    print(f"Download complete. Log saved to {log_file}")

if __name__ == "__main__":
    main()
