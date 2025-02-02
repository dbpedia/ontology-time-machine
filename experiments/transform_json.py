import json
import os

def transform_json(input_file_path, output_file_path):
    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"The file {input_file_path} does not exist.")

    with open(input_file_path, "r") as file:
        data = json.load(file)

    for entry in data:
        for download in entry.get("downloads", {}).values():
            if "headers" in download and isinstance(download["headers"], dict):
                download["headers"] = "\n".join(f"{k}: {v}" for k, v in download["headers"].items())
            if "error" in download and download["error"] and "chain_details" in download["error"]:
                chain_details = download["error"]["chain_details"]
                if isinstance(chain_details, list):
                    download["error"]["chain_details"] = "\n".join(
                        f"{item['type']}: {item['message']}" for item in chain_details
                    )
            if "rapper_error" in download and download["rapper_error"]:
                rapper_error_lines = download["rapper_error"].splitlines()
                if len(rapper_error_lines) > 11:
                    download["rapper_error"] = "\n".join(rapper_error_lines[:6] + ["..."] + rapper_error_lines[-5:])

    with open(output_file_path, "w") as file:
        json.dump(data, file, indent=4)

def main():
    input_json_file = "downloads-200ms-shuffled/download_log_extended.json"
    output_json_file = "downloads-200ms-shuffled/download_log_extended_flattened.json"
    transform_json(input_json_file, output_json_file)
    print(f"Transformation complete. File saved to {output_json_file}")

if __name__ == "__main__":
    main()
