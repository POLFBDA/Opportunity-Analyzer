import os
import pandas as pd
import requests
import json
import argparse
import uuid
from datetime import datetime
import pytz
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

cache_file = "ollama_suggestion_cache.json"
summary_folder = "summary"
input_folder = "input"
output_folder = "output"


# Load cache from a JSON file
def load_cache(cache_file):
    logging.debug("Loading cache from %s", cache_file)
    if os.path.exists(cache_file):
        with open(cache_file, "r") as file:
            return json.load(file)
    else:
        return {}


# Save the cache to a JSON file
def save_cache(cache, cache_file):
    logging.debug("Saving cache to %s", cache_file)
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
    Analyze the following AWS Well-Architected Review finding and suggest AWS solutions that can be implemented to directly address the issue described:

    Pillar: {cache_entry['Pillar']}
    Question: {cache_entry['Question']}
    Severity: {cache_entry['Severity']}
    Check Title: {cache_entry['Check Title']}
    Check Description: {cache_entry['Check Description']}
    Resource Type: {cache_entry['Resource Type']}

    {refresh_note}
    {additional_info_note}
    """

    logging.info(
        f"Sending the following prompt to Ollama for Check ID: {check_id}\n{analysis_prompt}"
    )

    # Interact with the local Ollama instance
    url = f"{ollama_host}/generate"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "gemma2:2b",  # Adjust this to the model you're using locally
        "prompt": analysis_prompt,
        "stream": False,  # Ensure streaming is disabled
    }

    logging.debug("Sending POST request to %s with payload: %s", url, payload)
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.headers.get("Content-Type", "").startswith("application/json"):
        try:
            response_json = response.json()
            if "response" in response_json:
                suggestion = response_json["response"].strip()
                logging.info(
                    f"New suggestion for Check Title '{cache_entry['Check Title']}': {suggestion}"
                )
                return suggestion
            else:
                logging.warning(
                    "No suggestion provided in response for Check ID: %s", check_id
                )
                return "No suggestion provided."
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON. Response was: %s", response.text)
            return f"Failed to parse JSON. Response was: {response.text}"
    else:
        logging.error("Unexpected response format for Check ID: %s", check_id)
        return "Unexpected response format."


# Generate trends summary per analyzed file
def generate_summary(df, filename):
    logging.debug("Generating summary for file: %s", filename)
    pst = pytz.timezone("America/Los_Angeles")
    timestamp = datetime.now(pst).strftime("%Y-%m-%d %H:%M:%S %Z")

    # Filter for failed checks only
    failed_checks_df = df[df["Status"].str.lower() == "failed"]

    # Group check titles by severity
    check_titles_with_severity = (
        failed_checks_df.groupby("Check Title")["Severity"].first().to_dict()
    )

    summary = {
        "filename": filename,
        "total_findings": len(df),
        "failed_findings": len(failed_checks_df),  # Count of failed findings
        "failed_pillar_counts": failed_checks_df["Pillar"].value_counts().to_dict(),
        "failed_severity_counts": failed_checks_df["Severity"].value_counts().to_dict(),
        "failed_check_title_counts": {
            title: {
                "count": count,
                "severity": check_titles_with_severity.get(title, "Unknown"),
            }
            for title, count in failed_checks_df["Check Title"].value_counts().items()
        },
        "timestamp": timestamp,  # Add the timestamp here
    }
    logging.debug("Summary generated: %s", summary)
    return summary


# Save the summary to a JSON file
def save_summary_to_json(summary, summary_json_path):
    logging.debug("Saving summary to JSON file: %s", summary_json_path)
    # Check if the file exists and load it, ensuring it's a list
    if os.path.exists(summary_json_path):
        with open(summary_json_path, "r") as file:
            try:
                existing_summary = json.load(file)
                # Ensure it's a list, otherwise reset it to an empty list
                if not isinstance(existing_summary, list):
                    logging.warning(
                        f"Warning: {summary_json_path} does not contain a list. Resetting it."
                    )
                    existing_summary = []
            except json.JSONDecodeError:
                logging.warning("Failed to decode %s. Resetting it.", summary_json_path)
                existing_summary = []
    else:
        existing_summary = []

    # Check if an entry for the filename already exists
    file_exists = False
    for entry in existing_summary:
        if entry["filename"] == summary["filename"]:
            # Update the existing entry
            entry.update(summary)
            file_exists = True
            break

    if not file_exists:
        # Add the new summary if the file wasn't found in existing entries
        existing_summary.append(summary)

    # Save the updated summary back to the JSON file
    with open(summary_json_path, "w") as file:
        json.dump(existing_summary, file, indent=4)

    logging.info(
        "Summary saved or updated for %s in %s", summary["filename"], summary_json_path
    )


# Save the summary to a CSV file using pd.concat
def save_summary_to_csv(summary, summary_file):
    logging.debug("Saving summary to CSV file: %s", summary_file)
    new_summary_df = pd.DataFrame([summary])

    if not os.path.exists(summary_file):
        new_summary_df.to_csv(summary_file, index=False)
    else:
        existing_summary = pd.read_csv(summary_file)

        # Check if an entry for the filename already exists in the CSV
        if summary["filename"] not in existing_summary["filename"].values:
            combined_summary = pd.concat(
                [existing_summary, new_summary_df], ignore_index=True
            )
            combined_summary.to_csv(summary_file, index=False)
            logging.info("Added summary for file %s", summary["filename"])
        else:
            # Update the existing entry in the DataFrame
            existing_summary.loc[
                existing_summary["filename"] == summary["filename"],
                new_summary_df.columns,
            ] = new_summary_df.values[0]
            existing_summary.to_csv(summary_file, index=False)
            logging.info("Updated summary for file %s", summary["filename"])


# Process all CSV files in the input folder and generate suggestions and summaries
def process_input_files(
    cache, input_folder, output_folder, summary_folder, save_interval=10
):
    logging.debug("Processing input files in folder: %s", input_folder)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        logging.debug("Created output folder: %s", output_folder)

    if not os.path.exists(summary_folder):
        os.makedirs(summary_folder)
        logging.debug("Created summary folder: %s", summary_folder)

    next_check_id = len(cache) + 1  # Start from the next available check ID

    # Track processed files to avoid duplicates
    processed_files = set()

    with os.scandir(input_folder) as entries:
        for entry in entries:
            if (
                entry.is_file()
                and entry.name.endswith(".csv")
                and entry.name not in processed_files
            ):
                input_path = entry.path
                logging.info("Processing file: %s", input_path)

                # Mark the file as processed
                processed_files.add(entry.name)

                # Load the CSV data, specifying that the header is in row 9 (index 8)
                logging.debug("Loading CSV data from %s", input_path)
                try:
                    df = pd.read_csv(input_path, header=8)

                    required_columns = [
                        "Serial number",
                        "Pillar",
                        "Severity",
                        "Status",
                        "Resource ID",
                        "Resource Name",
                        "Resource Type",
                        "Question",
                        "Check Title",
                        "Check Description",
                        "Account Name",
                        "Account ID",
                        "Region",
                    ]

                    # Check if all required columns are present
                    if not all(col in df.columns for col in required_columns):
                        missing_cols = [
                            col for col in required_columns if col not in df.columns
                        ]
                        logging.warning(
                            f"Missing required columns {missing_cols} in file {input_path}. Skipping file."
                        )
                        continue

                    # Track the number of new suggestions generated
                    new_suggestions_count = 0

                    # Process each finding in the CSV
                    suggestions = []
                    for index, row in df.iterrows():
                        check_title = row["Check Title"]

                        # Check if suggestion exists in cache
                        if check_title in cache:
                            suggestions.append(cache[check_title]["suggestion"])
                            logging.info(
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
                                "Status": row["Status"],
                                "Resource Type": row["Resource Type"],
                                "Check Title": check_title,
                                "Check Description": row["Check Description"],
                                "suggestion": suggestion,
                            }
                            next_check_id += 1  # Increment check ID
                            new_suggestions_count += (
                                1  # Increment new suggestions counter
                            )

                        # Save the cache and log message after every 10 new suggestions
                        if new_suggestions_count >= 10:
                            save_cache(cache, cache_file)
                            logging.info(
                                f"Cache saved after {new_suggestions_count} new suggestions (total findings processed: {index + 1})."
                            )
                            new_suggestions_count = 0  # Reset the counter

                    # Get the current timestamp to append to the output file name
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                    # Save the new CSV with suggestions
                    output_filename = (
                        f"{entry.name.split('.')[0]}_{timestamp}_output.csv"
                    )
                    output_path = os.path.join(output_folder, output_filename)
                    df["Elastic Engineering Suggestions"] = suggestions
                    df.to_csv(output_path, index=False, encoding="utf-8-sig")
                    logging.info(f"CSV file saved with suggestions at {output_path}")

                    # Generate and save summary for the file (without suggestions)
                    summary = generate_summary(df, entry.name)

                    # Save summary as both JSON and CSV
                    save_summary_to_json(
                        summary, os.path.join(summary_folder, "summary.json")
                    )
                    save_summary_to_csv(
                        summary, os.path.join(summary_folder, "summary.csv")
                    )

                except Exception as e:
                    logging.error(f"Error processing file {input_path}: {e}")


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
        logging.info(f"Updating suggestions for Check IDs: {args.update_check_ids}")
        suggestion_cache = update_cache_for_check_ids(
            args.update_check_ids,
            suggestion_cache,
            additional_info=args.additional_info,
        )
        save_cache(suggestion_cache, cache_file)
        logging.info("Cache updated with new suggestions.")
    else:
        # Otherwise, process input files and generate new suggestions and summaries
        process_input_files(
            suggestion_cache, args.input_folder, args.output_folder, args.summary_folder
        )
        # Save the cache after processing all files
        save_cache(suggestion_cache, cache_file)


if __name__ == "__main__":
    main()
