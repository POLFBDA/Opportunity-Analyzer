import os
import json
import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

summary_folder = "summary"
summary_json_file = os.path.join(summary_folder, "summary.json")
output_json_file = os.path.join(summary_folder, "summary-analyze.json")
cache_file = "/mnt/data/ollama_suggestion_cache.json"
print(summary_json_file)


# Load summaries from the summary JSON file
def load_summary(summary_json_file):
    if os.path.exists(summary_json_file):
        with open(summary_json_file, "r") as file:
            try:
                summaries = json.load(file)
                if not isinstance(summaries, list):
                    logging.warning(
                        f"Warning: {summary_json_file} does not contain a list. Resetting it."
                    )
                    summaries = []
            except json.JSONDecodeError:
                logging.warning("Failed to decode %s. Resetting it.", summary_json_file)
                summaries = []
    else:
        summaries = []
    return summaries


# Load the severity data from the suggestion cache
def load_suggestion_cache(cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, "r") as file:
            try:
                suggestion_cache = json.load(file)
            except json.JSONDecodeError:
                logging.warning(
                    "Failed to decode %s. Returning empty dictionary.", cache_file
                )
                suggestion_cache = {}
    else:
        suggestion_cache = {}
    return suggestion_cache


# Analyze trends across multiple files and save results to a new JSON file
def analyze_trends(summaries):
    if not summaries:
        logging.info("No summaries found to analyze.")
        return

    # Calculate total findings and failed findings across all files
    total_findings = sum(summary.get("total_findings", 0) for summary in summaries)
    total_failed_findings = sum(
        summary.get("failed_findings", 0) for summary in summaries
    )

    # Initialize dictionaries to store combined counts
    combined_pillar_counts = {}
    combined_severity_counts = {}
    severity_grouped_check_title_counts = {}

    # Iterate through each summary and aggregate the counts
    for summary in summaries:
        # Aggregate pillar counts
        pillar_counts = summary.get("failed_pillar_counts", {})
        for pillar, count in pillar_counts.items():
            combined_pillar_counts[pillar] = (
                combined_pillar_counts.get(pillar, 0) + count
            )

        # Aggregate severity counts
        severity_counts = summary.get("failed_severity_counts", {})
        for severity, count in severity_counts.items():
            combined_severity_counts[severity] = (
                combined_severity_counts.get(severity, 0) + count
            )

        # Aggregate check title counts grouped by severity
        check_title_counts = summary.get("failed_check_title_counts", {})
        for title, details in check_title_counts.items():
            count = details.get("count", 0)
            severity = details.get("severity", "Unknown")

            # Initialize the severity group if not already present
            if severity not in severity_grouped_check_title_counts:
                severity_grouped_check_title_counts[severity] = {}

            # Add or update the check title count under the appropriate severity
            if title not in severity_grouped_check_title_counts[severity]:
                severity_grouped_check_title_counts[severity][title] = 0
            severity_grouped_check_title_counts[severity][title] += count

    # Convert aggregated data to pandas Series for better display
    pillar_counts_series = pd.Series(combined_pillar_counts).sort_values(
        ascending=False
    )
    severity_counts_series = pd.Series(combined_severity_counts).sort_values(
        ascending=False
    )

    # Print insights
    print("\nSummary Insights Across All Files:")
    print(f"Total Findings Analyzed: {total_findings}")
    print(f"Total Failed Findings: {total_failed_findings}")
    print("\nTotal Pillars by Pillar Type:")
    print(pillar_counts_series.to_string())
    print("\nTotal Severity by Severity Type:")
    print(severity_counts_series.to_string())
    print("\nCheck Titles Grouped by Severity:")
    for severity, titles in severity_grouped_check_title_counts.items():
        print(f"\nSeverity: {severity}")
        for title, count in titles.items():
            print(f"  {title}: {count}")

    # Create a summary dictionary to save as JSON
    summary_data = {
        "total_findings": total_findings,
        "total_failed_findings": total_failed_findings,
        "pillar_counts": combined_pillar_counts,
        "severity_counts": combined_severity_counts,
        "check_title_counts": severity_grouped_check_title_counts,
    }

    # Save the summary data to a new JSON file
    with open(output_json_file, "w") as outfile:
        json.dump(summary_data, outfile, indent=4)

    print("\nSummary data saved to", output_json_file)


# Main function to run the program
def main():
    # Load summaries from JSON file
    summaries = load_summary(summary_json_file)

    # Load suggestion cache
    suggestion_cache = load_suggestion_cache(cache_file)

    # Analyze trends across summaries and save the results
    analyze_trends(summaries)


if __name__ == "__main__":
    main()
