import pandas as pd
import requests
import json
import os


# Load the CSV data
def load_csv(file_path):
    return pd.read_csv(file_path)


# Analyze each finding using Ollama
def analyze_finding_with_ollama(row):
    # Use the host.docker.internal address for dev containers
    ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434/api")

    # Compose the analysis prompt for each finding
    analysis_prompt = f"""
    Analyze the following Well-Architected Review finding:

    Pillar: {row['Pillar']}
    Question: {row['Question']}
    Severity: {row['Severity']}
    Check Title: {row['Check Title']}
    Check Description: {row['Check Description']}
    Resource Type: {row['Resource Type']}

    Based on this information, identify potential opportunities for DevOps consultants to provide Elastic Engineering services that could optimize cloud infrastructure, enhance automation, reduce costs, or improve security. If there are risks associated with the changes you are suggesting, note them. If there are any cost implications, note them.
    """

    print(f"Sending the following prompt to Ollama:\n{analysis_prompt}")

    # Interact with the local Ollama instance
    url = f"{ollama_host}/generate"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "llama3.1:8b",  # Adjust this to the model you're using locally
        "prompt": analysis_prompt,
        "stream": False,  # Ensure streaming is disabled
    }

    # Send the request
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Log the raw response for debugging
    # print(f"Raw response from Ollama: {response.text}")

    # Parse the response and extract the "response" field
    if response.headers.get("Content-Type", "").startswith("application/json"):
        try:
            # Parse the JSON response
            response_json = response.json()

            # Extract the text under the "response" key if it exists
            if "response" in response_json:
                suggestion = response_json[
                    "response"
                ].strip()  # Clean and return the suggestion
                print(suggestion)
                return suggestion
            else:
                return "No suggestion provided."
        except json.JSONDecodeError:
            print(f"Failed to parse JSON. Response was: {response.text}")
            return f"Failed to parse JSON. Response was: {response.text}"
    else:
        print("Unexpected response format.")
        return "Unexpected response format."


# Generate suggestions for each finding
def generate_suggestions_for_all_findings(df):
    suggestions = []
    for index, row in df.iterrows():
        print(f"Analyzing finding {index + 1}/{len(df)}...")
        suggestion = analyze_finding_with_ollama(row)
        suggestions.append(suggestion)  # Append suggestion as is
    return suggestions


# Save the new CSV with suggestions
def save_csv_with_suggestions(df, suggestions, output_path):
    # Add the suggestions as a new column to the dataframe
    df["Elastic Engineering Suggestions"] = suggestions
    df.to_csv(
        output_path, index=False, encoding="utf-8-sig"
    )  # Ensure proper encoding for special characters
    print(f"CSV file saved with suggestions at {output_path}")


# Main function to run the program
def main():
    # Path to the CSV file
    file_path = "generated_well_architected_findings.csv"
    output_path = "findings_with_suggestions.csv"

    # Load the CSV data
    df = load_csv(file_path)

    # Generate suggestions for each finding
    suggestions = generate_suggestions_for_all_findings(df)

    # Save the new CSV with suggestions
    save_csv_with_suggestions(df, suggestions, output_path)


if __name__ == "__main__":
    main()
