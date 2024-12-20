import json
import subprocess
import os
import re

ontology_map = {
    'nt': 'ntriples',
    'ttl': 'turtle',
    'rdfxml': 'rdfxml'
}

def process_ontologies(json_file_path, output_file_path):
    def is_uri_in_subject(triples, ontology_uri):
        """
        Check if the ontology URI appears in the subject position of any triple.
        """
        subject_pattern = re.compile(rf"^<{re.escape(ontology_uri)}>")
        return any(subject_pattern.match(triple) for triple in triples)
    
    def format_error_message(error_message):
        lines = error_message.splitlines()
        if len(lines) > 20:
            return "\n".join(lines[:10] + ["\n\n\n............\n\n\n"] + lines[-10:])
        return error_message
    
    # Load the JSON file
    with open(json_file_path, 'r') as f:
        ontologies = json.load(f)
    
    base_folder = os.path.dirname(json_file_path)
    input_base_folder = os.path.basename(base_folder)
    
    for ontology in ontologies:
        ontology_url = ontology["url"]
        print(f'URL: {ontology_url}')
        for format_type, format_data in ontology["downloads"].items():
            # Extract the file path and format
            file_path = format_data.get("file_path")
            status_code = format_data.get("status_code")
            if not file_path:
                format_data["parsed_triples"] = None
                format_data["uri_in_subject_position"] = None
                format_data["rapper_error"] = None
            elif file_path and status_code == 200:
                file_path_parts = file_path.split(os.sep)
                file_path_parts[0] = input_base_folder
                file_path = os.sep.join(file_path_parts)
                # Prepare the command
                command = [
                    "cat",
                    file_path,
                    "|",
                    "rapper",
                    f"-i {ontology_map[format_type]}",
                    f"-o ntriples",
                    "-",
                    ontology_url
                ]
                print(" ".join(command))

                # Execute the command
                try:
                    result = subprocess.run(
                        " ".join(command),
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    
                    # Check the result and update the JSON
                    output = result.stdout
                    triples = output.splitlines()
                    num_triples = output.count("\n")
                    
                    uri_in_subject = is_uri_in_subject(triples, ontology_url)
                    format_data["uri_in_subject_position"] = uri_in_subject
                    format_data["parsed_triples"] = num_triples

                    if result.returncode == 0:
                        format_data["rapper_error"] = None
                    else:
                        format_data["rapper_error"] = format_error_message(result.stderr.strip())

                except Exception as e:
                    format_data["parsed_triples"] = 0
                    format_data["uri_in_subject_position"] = False
                    format_data["rapper_error"] = str(e)
    
    # Save the updated JSON
    with open(output_file_path, 'w') as f:
        json.dump(ontologies, f, indent=4)

if __name__ == "__main__":
    # Replace these paths with your actual file paths
    input_json_path = "downloads_direct_requests/download_log.json"
    output_json_path = "downloads_direct_requests/download_log_fixshort.json"

    if os.path.exists(input_json_path):
        process_ontologies(input_json_path, output_json_path)
        print(f"Processed ontologies. Updated JSON saved to {output_json_path}")
    else:
        print(f"Input file {input_json_path} not found.")
