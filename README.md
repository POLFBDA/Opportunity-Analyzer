# Opportunity-Analyzer

This project analyzes AWS Well-Architected Review findings using a local Ollama instance to generate suggestions for DevOps consultants. The Python script processes CSV data, sends each finding to the Ollama model, and retrieves suggestions to optimize cloud infrastructure, enhance automation, reduce costs, or improve security.

## Prerequisites

### General Requirements
- **Python 3.8+** (Ensure that Python and `pip` are installed)
- **Ollama** (Local large language model inference server)
- **Pandas** library to handle CSV data
- **Requests** library to communicate with the Ollama server

### Installing Dependencies
Run the following command to install the required Python libraries:
```bash
pip install pandas requests
```

### Ollama Installation
1. **Download and install Ollama** from the [Ollama website](https://ollama.com).
   
2. **Run Ollama:**
   To serve models locally, use the following command:
   ```bash
   ollama serve
   ```

3. **Set up the environment variable:**
   To specify which model to use in Ollama, you may need to set the model based on your platform.

---

## Development Environment Setup (Dev Container)

This project is set up to run in a **VS Code dev container** to simplify development and ensure consistent environments. The dev container includes Python, necessary libraries, and Docker integration for running Ollama.

### Steps to Use Dev Container

1. **Install Docker**:
   Ensure Docker is installed and running on your system.
   
   - For installation instructions, visit [Docker's official website](https://www.docker.com/get-started).

2. **Install VS Code Dev Containers Extension**:
   Install the **Dev Containers** extension in VS Code by searching for "Dev Containers" in the Extensions marketplace.

3. **Open in Dev Container**:
   - Clone this repository.
   - Open the project folder in VS Code.
   - VS Code should automatically prompt you to reopen the project in a dev container. If not, you can manually do it by:
     - Clicking on the **Remote Explorer** button on the bottom-left corner.
     - Selecting **Reopen in Container**.

4. **Ollama in Dev Container**:
   Ensure that Ollama is accessible inside the dev container by binding the container to a specific port when launching the dev container:
   
   Example (if running via Docker directly):
   ```bash
   docker run -p 11434:11434 your-dev-container
   ```

5. **Host Access in Dev Container**:
   When working with a dev container, ensure that the `OLLAMA_HOST` environment variable is set correctly, usually to `host.docker.internal`:
   
   ```bash
   export OLLAMA_HOST=http://host.docker.internal:11434
   ```

---

## Usage Instructions

### 1. Clone or Download the Repository

Clone the repository to your local machine:
```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. CSV Input Format

Prepare a CSV file named `generated_well_architected_findings.csv` with the following columns:
- `Pillar`
- `Question`
- `Severity`
- `Check Title`
- `Check Description`
- `Resource Type`

### 3. Ollama Model Selection

You can use different Ollama models based on your needs. Here are some example models that you can use by adjusting the following part of the Python script:

```python
# Interact with the local Ollama instance
url = f"{ollama_host}/generate"
headers = {"Content-Type": "application/json"}
payload = {
    "model": "gemma2:2b",  # Adjust this to the model you're using locally
    "prompt": analysis_prompt,
    "stream": False,  # Ensure streaming is disabled
}
```

#### Example Models:
- **gemma2:2b**: A general-purpose model for analyzing findings.
- **llama3.1:8b**: A larger model, potentially more accurate but resource-intensive.
- **llama3.1:latest**: The latest version of the llama model for the best current performance.
- **gemma2:13b**: A more advanced version of gemma2, useful for complex analysis.

You can replace the `"model"` field in the `payload` dictionary with any of these model names to suit your needs.

### 4. Run the Python Script

Make sure Ollama is running on your local machine, then run the Python script:

```bash
python analyzer.py [OPTIONS]
```

### 5. Available Flags for the Python Script

The script accepts the following optional flags:

- `--update-check-ids`: Specify one or more check IDs to update in the cache.
  ```bash
  python analyzer.py --update-check-ids 1 2 3
  ```
- `--additional-info`: Provide additional information to append to the prompt when updating suggestions.
  ```bash
  python analyzer.py --update-check-ids 1 --additional-info "New compliance requirements"
  ```
- `--input-folder`: Specify a custom folder containing input CSV files. Default is `input`.
  ```bash
  python analyzer.py --input-folder custom_input_folder
  ```
- `--output-folder`: Specify a custom folder to save output files. Default is `output`.
  ```bash
  python analyzer.py --output-folder custom_output_folder
  ```
- `--summary-folder`: Specify a custom folder to save summary files. Default is `summary`.
  ```bash
  python analyzer.py --summary-folder custom_summary_folder
  ```

### 6. Output

The script will:
- Read the `generated_well_architected_findings.csv` file.
- Send each finding to Ollama for analysis.
- Save the suggestions in a new column named `Elastic Engineering Suggestions` in a new CSV file named `findings_with_suggestions.csv`.
- Update the `ollama_suggestion_cache.json` file with new or refreshed suggestions to maintain a record of previously processed findings.
- Generate summary files for analyzed data and save them in JSON (`summary.json`) and CSV (`summary.csv`) formats in the specified summary folder.

---

## Environment Configuration

### On Windows:
To ensure that Ollama works as expected on Windows, make sure you set the following:
1. Set the `OLLAMA_HOST` environment variable (if running Ollama inside a dev container):
   ```bash
   set $env:OLLAMA_HOST="0.0.0.0"
   ```
2. Run Ollama:
   ```bash
   ollama serve
   ```

### On macOS:
To ensure that Ollama works as expected on macOS:
1. Run Ollama:
   ```bash
   OLLAMA_HOST=0.0.0.0 ollama serve
   ```

## Sample Commands

- **Run Ollama locally**:
  ```bash
  ollama serve
  ```

- **Running the Python script**:
  ```bash
  python analyzer.py
  ```

---

## Running Unit Tests

Unit tests are stored in the `tests/` directory. To run the unit tests, use the following command from the root directory of the project:

```bash
python -m unittest discover -s tests
```

This command will automatically discover and execute all the unit tests in the `tests` folder, including the test for refreshing cache items (`test_cache_refresh.py`).

### Additional Notes:
- **Docker Containers**: If you're using Docker, ensure that the container has access to the host's port `11434`.
- **Model Names**: You can check the list of installed models by running `ollama models` to ensure you are using the correct one.