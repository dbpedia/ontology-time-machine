import json
from collections import defaultdict

# Content type mapping for each format
content_type_mapping = {
    "ttl": "text/turtle",
    "nt": "application/n-triples",
    "rdfxml": "application/rdf+xml",
}

# Load the JSON data from the correct file path
file_path = 'downloads-200ms-shuffled/download_log_extended.json'
with open(file_path, 'r') as f:
    data = json.load(f)

# Initialize the aggregation dictionary for both proxy and no-proxy scenarios
aggregation = {
    "w/o proxy": defaultdict(lambda: defaultdict(int)),
    "with proxy": defaultdict(lambda: defaultdict(int)),
}

# Define categories for table
categories = [
    "unsuccessful payload retrieval",
    "DNS issue",
    "Con. / transport issue",
    "TLS cert issue",
    "Too many redirects",
    "Non-200 HTTP code",
    "Successful request (code 200)",
    "0 bytes content",
    "no rdf content (0 triples parsable)",
    "partially parsable rdf-content",
    "fully parsable rdf-content",
    "describes requested ont.",
    "no RDF mimetype",
    "confused RDF mimetype",
    "correct mimetype",
]

# Map error types to categories
error_mapping = {
    "NameResolutionError": "DNS issue",
    "ConnectionError": "Con. / transport issue",
    "TimeoutError": "Con. / transport issue",
    "ConnectTimeoutError": "Con. / transport issue",
    "NewConnectionError": "Con. / transport issue",
    "ReadTimeoutError": "Con. / transport issue",
    "RemoteDisconnected": "Con. / transport issue",
    "SSLError": "TLS cert issue",
    "TooManyRedirects": "Too many redirects",
    "HTTPError": "Non-200 HTTP code",
}

# Process each entry in the JSON data
for entry in data:
    url = entry.get("url", "")
    downloads = entry.get("downloads", {})
    
    for format, details in downloads.items():
        # Check if proxy was used
        is_proxy = details.get("proxy_used", False)
        proxy_key = "with proxy" if is_proxy else "w/o proxy"

        # Extract details
        status_code = details.get("status_code")
        parsed_triples = details.get("parsed_triples", 0)
        content_length = details.get("content_lenght_measured", 0)
        content_type = details.get("content_type", "").lower() if details.get("content_type") else None
        uri_in_subject_position = details.get("uri_in_subject_position", False)
        rapper_error = details.get("rapper_error")
        error = details.get("error", {})
        
        # Check for errors and categorize them
        if error and error.get("type_more_specific"):
            error_type = error["type_more_specific"]
            category = error_mapping.get(error_type, None)
            if category:
                aggregation[proxy_key][category][format] += 1
                aggregation[proxy_key]["unsuccessful payload retrieval"][format] += 1
            else:
                # Print uncategorized errors
                print(f"Uncategorized error type_more_specific: {error_type}")
            continue

        # Handle non-200 status codes
        if status_code != 200:
            aggregation[proxy_key]["Non-200 HTTP code"][format] += 1
            aggregation[proxy_key]["unsuccessful payload retrieval"][format] += 1
            continue

        # Successful request (status code 200)
        aggregation[proxy_key]["Successful request (code 200)"][format] += 1

        # Check for partially parsable RDF-content
        if parsed_triples > 0 and rapper_error:
            aggregation[proxy_key]["partially parsable rdf-content"][format] += 1
            continue

        # Count content conditions for successful requests
        if content_length == 0:
            aggregation[proxy_key]["0 bytes content"][format] += 1
        elif parsed_triples == 0:
            aggregation[proxy_key]["no rdf content (0 triples parsable)"][format] += 1
        elif parsed_triples >= 1000:
            aggregation[proxy_key]["fully parsable rdf-content"][format] += 1
            if uri_in_subject_position:
                aggregation[proxy_key]["describes requested ont."][format] += 1
                # Check MIME types for describing ontologies
                if content_type == content_type_mapping.get(format, ""):
                    aggregation[proxy_key]["correct mimetype"][format] += 1
                elif content_type in content_type_mapping.values():
                    aggregation[proxy_key]["confused RDF mimetype"][format] += 1
                else:
                    aggregation[proxy_key]["no RDF mimetype"][format] += 1

# Print the table
table_headers = ["Accessibility Status", "turtle", "ntriples", "rdfxml"]
for proxy_key in ["w/o proxy", "with proxy"]:
    print(f"\nRequested format {proxy_key}")
    print(f"{table_headers[0]:<40} {table_headers[1]:<10} {table_headers[2]:<10} {table_headers[3]:<10}")
    for category in categories:
        row = [category]
        for format in ["ttl", "nt", "rdfxml"]:
            row.append(aggregation[proxy_key][category].get(format, 0))
        print(f"{row[0]:<40} {row[1]:<10} {row[2]:<10} {row[3]:<10}")
