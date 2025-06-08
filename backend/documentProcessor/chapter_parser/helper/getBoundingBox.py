import base64
import os
import requests
import json


def getBoundingBox(input_pdf_path, output_directory, azure_endpoint, azure_api_key, azure_model_id):
    output_json_path = os.path.join(output_directory, "bounding_box.json")
    os.makedirs(output_directory, exist_ok=True)

    # Read and encode the PDF
    try:
        with open(input_pdf_path, "rb") as pdf_file:
            pdf_base64 = base64.b64encode(pdf_file.read()).decode("utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Input PDF not found: {input_pdf_path}")

    # Prepare the payload
    payload = {
        "model": azure_model_id,
        "document": f"data:application/pdf;base64,{pdf_base64}"
    }

    headers = {
        "Authorization": f"Bearer {azure_api_key}",
        "Content-Type": "application/json"
    }

    # Make API request
    try:
        response = requests.post(azure_endpoint, headers=headers, json=payload)
        response.raise_for_status()  # Raises exception for HTTP errors

        # Save the JSON response
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=4)

        print(f"Response successfully saved to {output_json_path}")
        return output_json_path

    except requests.exceptions.RequestException as e:
        print(f"Error during Azure API request: {e}")
        return None
