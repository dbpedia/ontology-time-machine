import requests
from urllib.parse import urlparse
from ontologytimemachine.custom_proxy import IP, PORT

# Mock proxy modes and settings for demonstration purposes
PROXY_MODES = ["live", "failover", "latest", "timestamp"]
INTERCEPTION_MODES = ["all", "archivo", "block"]



PROXY = f"{IP}:{PORT}"
HTTP_PROXY = f"http://{PROXY}"
HTTPS_PROXY = f"http://{PROXY}"
PROXIES = {"http": HTTP_PROXY, "https": HTTPS_PROXY}

# Load the TSV data
def load_tsv_data(tsv_file):
    iri_data = []
    with open(tsv_file, 'r') as f:
        for line in f.readlines()[1:]:
            parts = line.strip().split('\t')
            iri_data.append({
                "iri": parts[0],
                "error_dimension": parts[1],
                "expected_error": parts[2],
                "iri_type": parts[3],
                "comment": parts[4] if len(parts) > 4 else ""
            })
    return iri_data

# Basic request function (direct or proxied)
def make_request(iri, proxy=None, mode=None):
    try:
        response = requests.get(iri, proxies=proxy if proxy else {})
        return response.status_code, response.text
    except requests.exceptions.RequestException as e:
        return "error", str(e)

# Test function for direct Archivo IRI requests
def test_DA(iri_data):
    for item in iri_data:
        if item["iri_type"] == "hash" or item["iri_type"] == "term":
            status, content = make_request(item["iri"])
            print(f"DA Request to {item['iri']}: Status {status}, Expected {item['expected_error']}")

# Test function for direct non-Archivo IRI requests
def test_DN(iri_data):
    for item in iri_data:
        if item["iri_type"] == "slash":
            status, content = make_request(item["iri"])
            print(f"DN Request to {item['iri']}: Status {status}, Expected {item['expected_error']}")

# Proxied Archivo requests with different modes
def test_PA(iri_data, mode):
    for item in iri_data:
        if item["iri_type"] == "hash" or item["iri_type"] == "term":
            status, content = make_request(item["iri"], proxy=PROXY)
            print(f"{mode}-PA Request to {item['iri']}: Status {status}, Expected {item['expected_error']}")

# Proxied non-Archivo requests with different modes
def test_PN(iri_data, mode):
    for item in iri_data:
        if item["iri_type"] == "slash":
            status, content = make_request(item["iri"], proxy=PROXY)
            print(f"{mode}-PN Request to {item['iri']}: Status {status}, Expected {item['expected_error']}")

# Main function to run the tests based on the proxy mode and interception settings
def run_tests(tsv_file, interception_mode="block"):
    iri_data = load_tsv_data(tsv_file)

    print("Running Direct Archivo (DA) Tests...")
    test_DA(iri_data)

    print("\nRunning Direct Non-Archivo (DN) Tests...")
    test_DN(iri_data)

    if interception_mode != "block":
        for mode in PROXY_MODES:
            print(f"\nRunning Proxied Archivo ({mode}-PA) Tests...")
            test_PA(iri_data, mode)

            print(f"\nRunning Proxied Non-Archivo ({mode}-PN) Tests...")
            test_PN(iri_data, mode)

# Example of running the tests
if __name__ == "__main__":
    tsv_file = "tests/archivo_test_IRIs.tsv"
    run_tests(tsv_file, interception_mode="archivo")
