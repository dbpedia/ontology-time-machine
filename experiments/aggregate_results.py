import json
from collections import defaultdict

# Content type mapping for each format
content_type_mapping = {
    "ttl": "text/turtle",
    "nt": "application/n-triples",
    "rdfxml": ["application/rdf+xml", "application/xml"],  # Updated to include multiple accepted types
}

rdf_mimtetypes = ['text/turtle', 'application/n-triples', 'application/rdf+xml', 'application/xml']

# File paths for the logs
no_proxy_file_path = 'downloads-200ms-shuffled/download_log_extended.json'
proxy_file_path = 'downloads_proxy_requests/download_proxy_log_extended.json'

# Load the JSON data for no-proxy and with-proxy scenarios
with open(no_proxy_file_path, 'r') as f:
    no_proxy_data = json.load(f)

with open(proxy_file_path, 'r') as f:
    proxy_data = json.load(f)

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
    "correct for all 3 formats",
]

# Error type to category mapping logic
def map_error_to_category(error_type, type_more_specific):
    if error_type == "TooManyRedirects":
        return "Too many redirects"
    elif error_type == "SSLError":
        return "TLS cert issue"
    elif error_type == "ConnectionError":
        if type_more_specific == "NameResolutionError":
            return "DNS issue"
        else:
            return "Con. / transport issue"
    elif error_type == "ConnectTimeout":
        return "Con. / transport issue"
    else:
        return "Con. / transport issue"

# Check if MIME type is valid for the format
def is_valid_mimetype(format, content_type):
    expected_types = content_type_mapping.get(format, [])
    if isinstance(expected_types, list):
        return content_type in expected_types
    return content_type == expected_types

# Process data for aggregation
def process_data(data, proxy_key):
    for entry in data:
        url = entry.get("url", "")
        downloads = entry.get("downloads", {})
        formats_correct = set()

        for format, details in downloads.items():
            # Extract details
            status_code = details.get("status_code")
            parsed_triples = details.get("parsed_triples", 0)
            content_length = details.get("content_lenght_measured", 0)
            content_type = details.get("content_type", "").lower() if details.get("content_type") else None
            uri_in_subject_position = details.get("uri_in_subject_position", False)
            rapper_error = details.get("rapper_error")
            error = details.get("error", {})
            
            # Check for errors and categorize them
            if error and error.get("type"):
                error_type = error["type"]
                type_more_specific = error.get("type_more_specific")
                category = map_error_to_category(error_type, type_more_specific)
                aggregation[proxy_key][category][format] += 1
                aggregation[proxy_key]["unsuccessful payload retrieval"][format] += 1
                continue

            # Handle non-200 status codes
            if status_code != 200:
                aggregation[proxy_key]["Non-200 HTTP code"][format] += 1
                aggregation[proxy_key]["unsuccessful payload retrieval"][format] += 1
                continue

            # Successful request (status code 200)
            aggregation[proxy_key]["Successful request (code 200)"][format] += 1

            # Categorize successful ontologies
            if content_length == 0:
                aggregation[proxy_key]["0 bytes content"][format] += 1
            elif parsed_triples == 0:
                aggregation[proxy_key]["no rdf content (0 triples parsable)"][format] += 1
            elif parsed_triples > 0 and rapper_error:
                aggregation[proxy_key]["partially parsable rdf-content"][format] += 1
                if uri_in_subject_position:
                    aggregation[proxy_key]["describes requested ont."][format] += 1
            elif parsed_triples > 0 and not rapper_error:
                aggregation[proxy_key]["fully parsable rdf-content"][format] += 1
                if uri_in_subject_position:
                    aggregation[proxy_key]["describes requested ont."][format] += 1

                    # Check MIME types only for ontologies that describe the requested ontology
                    if content_type and is_valid_mimetype(format, content_type):
                        aggregation[proxy_key]["correct mimetype"][format] += 1
                        formats_correct.add(format)
                    elif content_type and content_type in rdf_mimtetypes:
                        aggregation[proxy_key]["confused RDF mimetype"][format] += 1
                    else:
                        aggregation[proxy_key]["no RDF mimetype"][format] += 1

        # Check if ontology is correct for all 3 formats
        if formats_correct == {"ttl", "nt", "rdfxml"}:
            aggregation[proxy_key]["correct for all 3 formats"]["all"] += 1

# Process both datasets
process_data(no_proxy_data, "w/o proxy")
process_data(proxy_data, "with proxy")

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
    # Print total for "correct for all 3 formats"
    correct_all = aggregation[proxy_key]["correct for all 3 formats"]["all"]
    print(f"{'correct for all 3 formats':<40} {correct_all:<10}")
