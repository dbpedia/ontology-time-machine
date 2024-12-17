import json
import subprocess
import os

ontology_map = {
    'nt': 'ntripes',
    'ttl': 'turtle',
    'rdfxml': 'rdfxml'
}

def process_ontologies(json_file_path, output_file_path):
    # Load the JSON file
    with open(json_file_path, 'r') as f:
        ontologies = json.load(f)
    
    for ontology in ontologies:
        print(f'URL: {ontology["url"]}')
        for format_type, format_data in ontology["downloads"].items():
            # Extract the file path and format
            file_path = format_data.get("file_path")
            status_code = format_data.get("status_code")
            if not file_path:
                format_data["parsed_triples"] = None
                format_data["rapper_error"] = None
            elif file_path and status_code == 200:
                file_path = file_path.replace('downloads_proxy-test', 'downloads_proxy-fixedCA')
                # Prepare the command
                command = [
                    "cat",
                    file_path,
                    "|",
                    "rapper",
                    f"-i {ontology_map[format_type]}",
                    f"-o ntriples",
                    "-",
                    ontology["url"]
                ]
                print(command)

                # Execute the command
                try:
                    result = subprocess.run(
                        " ".join(command),
                        shell=True,
                        capture_output=True,
                        text=True
                    )

                    # Check the result and update the JSON
                    if result.returncode == 0:
                        output = result.stdout
                        num_triples = output.count("\n")
                        format_data["parsed_triples"] = num_triples
                        format_data["rapper_error"] = None
                    else:
                        format_data["parsed_triples"] = 0
                        format_data["rapper_error"] = result.stderr.strip()

                except Exception as e:
                    format_data["parsed_triples"] = 0
                    format_data["rapper_error"] = str(e)
    
    # Save the updated JSON
    with open(output_file_path, 'w') as f:
        json.dump(ontologies, f, indent=4)

if __name__ == "__main__":
    # Replace these paths with your actual file paths
    input_json_path = "downloads_proxy-fixedCA/download_nt_proxy_log.json"
    output_json_path = "downloads_proxy-fixedCA/download_nt_proxy_log_extended.json"

    if os.path.exists(input_json_path):
        process_ontologies(input_json_path, output_json_path)
        print(f"Processed ontologies. Updated JSON saved to {output_json_path}")
    else:
        print(f"Input file {input_json_path} not found.")
