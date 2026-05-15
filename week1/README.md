# Week 1 ETL Pipeline

## Project Description

This project is a local ETL pipeline for ingesting raw HTML/MHTML job posting files, transforming them into structured JSON, loading the cleaned data into a gold-stage artifact, and running a simple profiling step. The goal is to demonstrate a practical data engineering workflow with separate bronze/silver/gold stages and provide a reproducible pipeline for web content extraction and validation.

## Setup Instructions

### Prerequisites

- Python 3.12 or later
- A POSIX-compatible shell on Linux/macOS
- `uv` package manager (recommended) or the ability to install Python packages with `pip`
- A local Git repository with this `README.md` at the root

### Environment setup

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Upgrade `pip` and install `uv` if it is not already installed:

```bash
python -m pip install --upgrade pip
python -m pip install uv
```

3. Install the project dependencies from `pyproject.toml`:

```bash
uv install
```

If you do not want to use `uv`, you can install the required packages directly:

```bash
python -m pip install -e .
```

### Environment variables

This project does not currently require any API keys or secret environment variables. If you add configuration later, store sensitive values in a local `.env` file or export them in the shell, and never commit secrets to Git.

## Usage

Run the pipeline from the repository root where `main.py` is located.

### Available commands

- `uv run python main.py ingest`
- `uv run python main.py process`
- `uv run python main.py load`
- `uv run python main.py profile`
- `uv run python main.py all`

If `uv` is not available, use:

```bash
python main.py ingest
python main.py process
python main.py load
python main.py profile
python main.py all
```

### Pipeline stages

- `ingest` reads source files from `data/test` and writes bronze-stage HTML data into `data/1_bronze`
- `process` reads bronze-stage data from `data/1_bronze` and writes silver-stage JSON into `data/2_silver`
- `load` reads silver-stage JSON from `data/2_silver` and writes gold-stage output into `data/3_gold` and `jobs.db`
- `profile` runs a profiling step on the final gold-stage database at `data/3_gold/jobs.db`
- `all` runs the full pipeline in sequence: ingest → process → load → profile

### Example

```bash
source .venv/bin/activate
uv run python main.py all
```

Expected behavior:

- The pipeline will read raw `.mhtml` files from `data/test`
- Bronze output appears in `data/1_bronze`
- Silver JSON output appears in `data/2_silver`
- Gold artifacts appear in `data/3_gold`
- The profiler reads the final SQLite database and prints summary results

## Technical Reflections

### How does this local pipeline map to industry practices?

This project follows a common industry ETL pattern with separate bronze, silver, and gold layers. The bronze layer captures raw ingestion, the silver layer transforms and validates structured data, and the gold layer prepares final, load-ready output. This mirrors production data engineering architectures that emphasize staged processing, traceability, and modular pipeline design.

### What are the strengths of this implementation?

The separation of concerns across `ingestor`, `processor`, `loader`, and `profiler` makes the code easier to test, maintain, and extend. Each stage uses clear directory inputs and outputs, which is a strong practice for building repeatable pipelines and supporting incremental reprocessing.

### What could be improved to make it more production-ready?

Adding configuration management, parameterized paths, and error handling would improve robustness. In a production environment, this project would also benefit from automated task orchestration, logging, and support for environment-specific settings rather than hard-coded directories.

