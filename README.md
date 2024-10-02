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

### 3. Model Differences Between Windows and macOS

**On Windows:**
- Use the model name `llama3.1:8b` when sending requests to Ollama.

**On macOS:**
- Use the model name `llama3.1:latest` when sending requests to Ollama.

The model name can be set dynamically based on your operating system in your Python script.

### 4. Modify the Python Script

The Python script reads a CSV file, processes each finding, and sends a request to the Ollama server to analyze the finding. You may need to set the correct model name based on your environment.

Here’s a snippet from the Python script that handles this:

```python
import platform

def get_model_name():
    if platform.system() == "Windows":
        return "llama3.1:8b"
    elif platform.system() == "Darwin":  # macOS
        return "llama3.1:latest"
    else:
        return "llama3.1:8b"  # Default for other platforms
```

### 5. Run the Python Script

Make sure Ollama is running on your local machine, then run the Python script:
```bash
python analyzer.py
```

### 6. Output

The script will:
- Read the `generated_well_architected_findings.csv` file.
- Send each finding to Ollama for analysis.
- Save the suggestions in a new column named `Elastic Engineering Suggestions` in a new CSV file named `findings_with_suggestions.csv`.

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
The model name and Ollama host setup differ slightly on macOS:
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

### Additional Notes:
- **Docker Containers**: If you're using Docker, ensure that the container has access to the host's port `11434`.
- **Model Names**: You can check the list of installed models by running `ollama models` to ensure you are using the correct one.
