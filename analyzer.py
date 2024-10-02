import os
import pandas as pd
import requests
import json
import argparse
import uuid


cache_file = "ollama_suggestion_cache.json"
summary_file = "summary.csv"
input_folder = "input"
output_folder = "output"


# Load cache from a JSON file
def load_cache(cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, "r") as file:
            return json.load(file)
    else:
        return {}


# Save the cache to a JSON file
def save_cache(cache, cache_file):
    with open(cache_file, "w") as file:
        json.dump(cache, file, indent=4)


# Analyze each finding using Ollama, with caching based on check ID
def analyze_finding_with_ollama(
    cache_entry, check_id, refresh=False, additional_info=None
):
    # Use the host.docker.internal address for dev containers
    ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434/api")

    # Dynamic prompt - add a refresh note if we're refreshing
    refresh_note = ""
    if refresh:
        refresh_note = "Important: Generate a new response and do not return the previous suggestion, even if you have seen this before."

    # Append additional info if provided
    additional_info_note = (
        f" Additional information: {additional_info}" if additional_info else ""
    )

    # Compose the analysis prompt for each finding
    analysis_prompt = f"""
    Analyze the following Well-Architected Review finding:

    Pillar: {cache_entry['Pillar']}
    Question: {cache_entry['Question']}
    Severity: {cache_entry['Severity']}
    Check Title: {cache_entry['Check Title']}
    Check Description: {cache_entry['Check Description']}
    Resource Type: {cache_entry['Resource Type']}

    Based on this information, identify potential opportunities for DevOps consultants to provide Elastic Engineering services that could optimize cloud infrastructure, enhance automation, reduce costs, or improve security. 
    {refresh_note}
    {additional_info_note}
    """

    print(
        f"Sending the following prompt to Ollama for Check ID: {check_id}\n{analysis_prompt}"
    )

    # Interact with the local Ollama instance
    url = f"{ollama_host}/generate"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "llama3.1:8b",  # Adjust this to the model you're using locally
        "prompt": analysis_prompt,
        "stream": False,  # Ensure streaming is disabled
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.headers.get("Content-Type", "").startswith("application/json"):
        try:
            response_json = response.json()
            if "response" in response_json:
                suggestion = response_json["response"].strip()
                print(
                    f"New suggestion for Check Title '{cache_entry['Check Title']}': {suggestion}"
                )
                return suggestion
            else:
                return "No suggestion provided."
        except json.JSONDecodeError:
            print(f"Failed to parse JSON. Response was: {response.text}")
            return f"Failed to parse JSON. Response was: {response.text}"
    else:
        print("Unexpected response format.")
        return "Unexpected response format."


# Generate trends summary per analyzed file
def generate_summary(df, filename):
    summary = {
        "filename": filename,
        "total_findings": len(df),
        "pillar_counts": df["Pillar"].value_counts().to_dict(),
        "severity_counts": df["Severity"].value_counts().to_dict(),
        "check_title_counts": df["Check Title"].value_counts().to_dict(),
    }
    return summary


# Save the summary to a CSV file using pd.concat
def save_summary_to_csv(summary, summary_file):
    new_summary_df = pd.DataFrame([summary])

    if not os.path.exists(summary_file):
        new_summary_df.to_csv(summary_file, index=False)
    else:
        existing_summary = pd.read_csv(summary_file)
        if summary["filename"] not in existing_summary["filename"].values:
            # Use pd.concat instead of append
            combined_summary = pd.concat(
                [existing_summary, new_summary_df], ignore_index=True
            )
            combined_summary.to_csv(summary_file, index=False)
            print(f"Added summary for file {summary['filename']}")
        else:
            print(f"File {summary['filename']} already exists in the summary.")


# Process all CSV files in the input folder and generate suggestions and summaries
def process_input_files(cache, input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    next_check_id = len(cache) + 1  # Start from the next available check ID

    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            input_path = os.path.join(input_folder, filename)
            print(f"Processing file: {input_path}")

            # Load the CSV data
            df = pd.read_csv(input_path)

            # Generate suggestions for each finding
            suggestions = []
            for index, row in df.iterrows():
                check_title = row["Check Title"]

                # Check if suggestion exists in cache
                if check_title in cache:
                    suggestions.append(cache[check_title]["suggestion"])
                    print(
                        f"Using cached suggestion for '{check_title}' (Check ID: {cache[check_title]['check_id']})"
                    )
                else:
                    # Analyze and store in cache
                    suggestion = analyze_finding_with_ollama(row, next_check_id)
                    suggestions.append(suggestion)
                    cache[check_title] = {
                        "check_id": str(next_check_id),
                        "Pillar": row["Pillar"],
                        "Question": row["Question"],
                        "Severity": row["Severity"],
                        "Check Title": check_title,
                        "Check Description": row["Check Description"],
                        "Resource Type": row["Resource Type"],
                        "suggestion": suggestion,
                    }
                    next_check_id += 1  # Increment check ID

            # Save the new CSV with suggestions
            df["Elastic Engineering Suggestions"] = suggestions
            output_filename = f"findings_with_suggestions_{uuid.uuid4()}.csv"
            output_path = os.path.join(output_folder, output_filename)
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"CSV file saved with suggestions at {output_path}")

            # Generate and save summary for the file (without suggestions)
            summary = generate_summary(df, filename)
            save_summary_to_csv(summary, summary_file)


# Update specific entries in the cache based on check_id
def update_cache_for_check_ids(
    update_check_ids, suggestion_cache, additional_info=None
):
    for check_id in update_check_ids:
        # Find the corresponding check title based on check_id
        cache_entry = None
        for title, entry in suggestion_cache.items():
            if entry.get("check_id") == str(check_id):
                cache_entry = entry
                break

        if cache_entry:
            print(f"Updating suggestion for Check ID: {check_id}")
            new_suggestion = analyze_finding_with_ollama(
                cache_entry, check_id, refresh=True, additional_info=additional_info
            )
            cache_entry["suggestion"] = new_suggestion
        else:
            print(f"Check ID {check_id} not found in cache. Skipping update.")

    return suggestion_cache


# Main function to run the program
def main():
    parser = argparse.ArgumentParser(
        description="Process CSV files and update suggestions in cache."
    )
    parser.add_argument(
        "--update-check-ids",
        nargs="+",
        type=int,
        help="Specify the check IDs to update in the cache.",
    )
    parser.add_argument(
        "--additional-info",
        type=str,
        help="Additional information to append to the prompt when updating suggestions.",
    )
    parser.add_argument(
        "--input-folder", default="input", help="Folder containing input CSV files."
    )
    parser.add_argument(
        "--output-folder", default="output", help="Folder to save output files."
    )

    args = parser.parse_args()

    # Load the existing cache
    suggestion_cache = load_cache(cache_file)

    if args.update_check_ids:
        # Update specific check IDs in the cache
        suggestion_cache = update_cache_for_check_ids(
            args.update_check_ids,
            suggestion_cache,
            additional_info=args.additional_info,
        )
        save_cache(suggestion_cache, cache_file)
        print(f"Cache updated for Check IDs: {args.update_check_ids}")
    else:
        # Process input files and generate suggestions
        process_input_files(suggestion_cache, args.input_folder, args.output_folder)
        save_cache(suggestion_cache, cache_file)
        print("All input files processed and cache saved.")


if __name__ == "__main__":
    main()
import os
import pandas as pd
import requests
import json
import argparse
import uuid
from datetime import datetime
import pytz


cache_file = "ollama_suggestion_cache.json"
summary_folder = "summary"
input_folder = "input"
output_folder = "output"


# Load cache from a JSON file
def load_cache(cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, "r") as file:
            return json.load(file)
    else:
        return {}


# Save the cache to a JSON file
def save_cache(cache, cache_file):
    with open(cache_file, "w") as file:
        json.dump(cache, file, indent=4)


# Analyze each finding using Ollama, with caching based on check ID
def analyze_finding_with_ollama(
    cache_entry, check_id, refresh=False, additional_info=None
):
    # Use the host.docker.internal address for dev containers
    ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434/api")

    # Dynamic prompt - add a refresh note if we're refreshing
    refresh_note = ""
    if refresh:
        refresh_note = "Important: Generate a new response and do not return the previous suggestion, even if you have seen this before."

    # Append additional info if provided
    additional_info_note = (
        f" Additional information: {additional_info}" if additional_info else ""
    )

    # Compose the analysis prompt for each finding
    analysis_prompt = f"""
    Analyze the following Well-Architected Review finding:

    Pillar: {cache_entry['Pillar']}
    Question: {cache_entry['Question']}
    Severity: {cache_entry['Severity']}
    Check Title: {cache_entry['Check Title']}
    Check Description: {cache_entry['Check Description']}
    Resource Type: {cache_entry['Resource Type']}

    Based on this information, identify potential opportunities for DevOps consultants to provide Elastic Engineering services that could optimize cloud infrastructure, enhance automation, reduce costs, or improve security. 
    {refresh_note}
    {additional_info_note}
    """

    print(
        f"Sending the following prompt to Ollama for Check ID: {check_id}\n{analysis_prompt}"
    )

    # Interact with the local Ollama instance
    url = f"{ollama_host}/generate"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "llama3.1:8b",  # Adjust this to the model you're using locally
        "prompt": analysis_prompt,
        "stream": False,  # Ensure streaming is disabled
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.headers.get("Content-Type", "").startswith("application/json"):
        try:
            response_json = response.json()
            if "response" in response_json:
                suggestion = response_json["response"].strip()
                print(
                    f"New suggestion for Check Title '{cache_entry['Check Title']}': {suggestion}"
                )
                return suggestion
            else:
                return "No suggestion provided."
        except json.JSONDecodeError:
            print(f"Failed to parse JSON. Response was: {response.text}")
            return f"Failed to parse JSON. Response was: {response.text}"
    else:
        print("Unexpected response format.")
        return "Unexpected response format."


# Generate trends summary per analyzed file
def generate_summary(df, filename):
    pst = pytz.timezone("America/Los_Angeles")
    timestamp = datetime.now(pst).strftime("%Y-%m-%d %H:%M:%S %Z")

    summary = {
        "filename": filename,
        "total_findings": len(df),
        "pillar_counts": df["Pillar"].value_counts().to_dict(),
        "severity_counts": df["Severity"].value_counts().to_dict(),
        "check_title_counts": df["Check Title"].value_counts().to_dict(),
        "timestamp": timestamp,  # Add the timestamp here
    }
    return summary


# Save the summary to a JSON file
def save_summary_to_json(summary, summary_json_path):
    if not os.path.exists(summary_json_path):
        with open(summary_json_path, "w") as file:
            json.dump([summary], file, indent=4)
    else:
        with open(summary_json_path, "r") as file:
            existing_summary = json.load(file)
        existing_summary.append(summary)
        with open(summary_json_path, "w") as file:
            json.dump(existing_summary, file, indent=4)
    print(f"Summary saved to {summary_json_path}")


# Save the summary to a CSV file using pd.concat
def save_summary_to_csv(summary, summary_file):
    new_summary_df = pd.DataFrame([summary])

    if not os.path.exists(summary_file):
        new_summary_df.to_csv(summary_file, index=False)
    else:
        existing_summary = pd.read_csv(summary_file)
        if summary["filename"] not in existing_summary["filename"].values:
            # Use pd.concat instead of append
            combined_summary = pd.concat(
                [existing_summary, new_summary_df], ignore_index=True
            )
            combined_summary.to_csv(summary_file, index=False)
            print(f"Added summary for file {summary['filename']}")
        else:
            print(f"File {summary['filename']} already exists in the summary.")


# Process all CSV files in the input folder and generate suggestions and summaries
def process_input_files(cache, input_folder, output_folder, summary_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not os.path.exists(summary_folder):
        os.makedirs(summary_folder)

    next_check_id = len(cache) + 1  # Start from the next available check ID

    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            input_path = os.path.join(input_folder, filename)
            print(f"Processing file: {input_path}")

            # Load the CSV data
            df = pd.read_csv(input_path)

            # Generate suggestions for each finding
            suggestions = []
            for index, row in df.iterrows():
                check_title = row["Check Title"]

                # Check if suggestion exists in cache
                if check_title in cache:
                    suggestions.append(cache[check_title]["suggestion"])
                    print(
                        f"Using cached suggestion for '{check_title}' (Check ID: {cache[check_title]['check_id']})"
                    )
                else:
                    # Analyze and store in cache
                    suggestion = analyze_finding_with_ollama(row, next_check_id)
                    suggestions.append(suggestion)
                    cache[check_title] = {
                        "check_id": str(next_check_id),
                        "Pillar": row["Pillar"],
                        "Question": row["Question"],
                        "Severity": row["Severity"],
                        "Check Title": check_title,
                        "Check Description": row["Check Description"],
                        "Resource Type": row["Resource Type"],
                        "suggestion": suggestion,
                    }
                    next_check_id += 1  # Increment check ID

            # Save the new CSV with suggestions
            df["Elastic Engineering Suggestions"] = suggestions
            output_filename = f"findings_with_suggestions_{uuid.uuid4()}.csv"
            output_path = os.path.join(output_folder, output_filename)
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"CSV file saved with suggestions at {output_path}")

            # Generate and save summary for the file (without suggestions)
            summary = generate_summary(df, filename)

            # Save summary as both JSON and CSV
            save_summary_to_json(summary, os.path.join(summary_folder, "summary.json"))
            save_summary_to_csv(summary, os.path.join(summary_folder, "summary.csv"))


# Update specific entries in the cache based on check_id
def update_cache_for_check_ids(
    update_check_ids, suggestion_cache, additional_info=None
):
    for check_id in update_check_ids:
        # Find the corresponding check title based on check_id
        cache_entry = None
        for title, entry in suggestion_cache.items():
            if entry.get("check_id") == str(check_id):
                cache_entry = entry
                break

        if cache_entry:
            print(f"Updating suggestion for Check ID: {check_id}")
            new_suggestion = analyze_finding_with_ollama(
                cache_entry, check_id, refresh=True, additional_info=additional_info
            )
            cache_entry["suggestion"] = new_suggestion
        else:
            print(f"Check ID {check_id} not found in cache. Skipping update.")

    return suggestion_cache


# Main function to run the program
def main():
    parser = argparse.ArgumentParser(
        description="Process CSV files and update suggestions in cache."
    )
    parser.add_argument(
        "--update-check-ids",
        nargs="+",
        type=int,
        help="Specify the check IDs to update in the cache.",
    )
    parser.add_argument(
        "--additional-info",
        type=str,
        help="Additional information to append to the prompt when updating suggestions.",
    )
    parser.add_argument(
        "--input-folder", default="input", help="Folder containing input CSV files."
    )
    parser.add_argument(
        "--output-folder", default="output", help="Folder to save output files."
    )
    parser.add_argument(
        "--summary-folder",
        default="summary",
        help="Folder to save summary files (JSON and CSV).",
    )

    args = parser.parse_args()

    # Load the existing cache
    suggestion_cache = load_cache(cache_file)

    if args.update_check_ids:
        # If the update-check-ids flag is used, only update the cache for the specified check IDs
        print(f"Updating suggestions for Check IDs: {args.update_check_ids}")
        suggestion_cache = update_cache_for_check_ids(
            args.update_check_ids,
            suggestion_cache,
            additional_info=args.additional_info,
        )
        save_cache(suggestion_cache, cache_file)
        print("Cache updated with new suggestions.")
    else:
        # Otherwise, process input files and generate new suggestions and summaries
        process_input_files(
            suggestion_cache, args.input_folder, args.output_folder, args.summary_folder
        )
        # Save the cache after processing all files
        save_cache(suggestion_cache, cache_file)


if __name__ == "__main__":
    main()
