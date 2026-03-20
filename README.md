# nf-downloadstats

[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A522.10.6-23aa62.svg)](https://www.nextflow.io/)
[![run with conda](https://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Launch on Seqera Platform](https://img.shields.io/badge/Launch%20%F0%9F%9A%80-Seqera%20Platform-%234256e7)](https://cloud.seqera.io/launch?pipeline=https://github.com/PRIDE-Archive/nf-downloadstats)

# Introduction

The pipeline is built using Nextflow, a workflow tool to run tasks across multiple compute infrastructures in a very portable manner.
This pipeline gets the statistics around file downloads from the log files saved in the EBI infrastructure.
It classifies download traffic into bots, institutional download hubs, and independent user downloads using [DeepLogBot](https://github.com/PRIDE-Archive/deeplogbot), helping to understand genuine usage of the files and projects, and aiding decision-making.

# Pipeline in Nutshell

## **Overview**
This pipeline automates log file retrieval, transformation, bot/hub/organic traffic classification, and statistical analysis, producing structured outputs for downstream analysis and database updates. It is optimized for high-throughput processing and large-scale data aggregation.

## **Workflow Steps**

1. **Retrieve Log Files (`get_log_files`)**
   - Identifies and compiles a list of log files from the root directory.
   - **Output:** `file_list.txt`

2. **Compute Log File Statistics (`run_log_file_stat`)**
   - Performs statistical analysis on extracted log files.
   - **Output:** `log_file_statistics.html`

3. **Process Log Files (`process_log_file`)**
   - Extracts and transforms log data into Parquet format.
   - **Output:** `*.parquet` files.

4. **Merge Parquet Datasets (`merge_parquet_files`)**
   - Aggregates individual Parquet datasets into a consolidated dataset.
   - **Output:** `output_parquet`

5. **Classify Bot Downloads (`classify_bot_downloads`) [Optional]**
   - Classifies download traffic into three categories using [DeepLogBot](https://github.com/PRIDE-Archive/deeplogbot):
     - **Bots**: Automated scrapers and coordinated botnets
     - **Institutional Hubs**: Legitimate bulk downloaders (research facilities, mirrors)
     - **Organic Users**: Independent individual researchers
   - Adds `is_bot`, `is_hub`, `is_organic`, `behavior_type`, and `confidence_score` columns to the parquet.
   - **Outputs:** `annotated_parquet`, `bot_classification_reports/`
   - **Enable:** Set `enable_bot_classification: true` in your params file.

6. **Analyze Merged Dataset (`analyze_parquet_files`)**
   - Conducts statistical analysis and generates JSON reports.
   - **Outputs:**
     - `project_level_download_counts.json`
     - `file_level_download_counts.json`
     - `project_level_yearly_download_counts.json`
     - `project_level_top_download_counts.json`
     - `all_data.json`

7. **Generate Download Statistics Report (`run_file_download_stat`)**
   - Produces a visual analytics report in HTML format.
   - **Output:** `file_download_stat.html`

8. **Push Report to Slack (`push_to_slack`)**
   - Uploads the HTML report to a Slack channel.
   - **Output:** `slack_push_status.txt`

9. **Update Project-Level Download Metrics (`update_project_download_counts`)**
   - Uploads project-level statistics to a database.
   - **Output:** `upload_response_file_downloads_per_project.txt`

10. **Update File-Level Download Metrics (`update_file_level_download_counts`)**
    - Segments large JSON datasets for database ingestion.
    - **Output:** Server response files confirming successful uploads.

## **Execution Flow**
```mermaid
flowchart TD;
    A[Retrieve Log Files] -->|file_list.txt| B[Compute Log File Statistics];
    A -->|file_list.txt| C[Process Log Files];
    C -->|*.parquet| D[Merge Parquet Datasets];
    D -->|output_parquet| E{Bot Classification Enabled?};
    E -->|Yes| F[Classify Bot Downloads];
    E -->|No| G[Analyze Merged Dataset];
    F -->|annotated_parquet| G;
    G -->|JSON Reports| H[Generate Download Statistics Report];
    H -->|file_download_stat.html| I[Push Report to Slack];
    G --> J[Update Project-Level Metrics];
    G --> K[Update File-Level Metrics];
```

## **Bot Classification**

The pipeline integrates [DeepLogBot](https://github.com/PRIDE-Archive/deeplogbot) to classify download traffic. Two classification methods are available:

| Method | Description | Speed | Requirements |
|--------|-------------|-------|-------------|
| `rules` | Hierarchical rule-based classification | Fast | Default dependencies |
| `deep` | ML-based (GradientBoosting meta-learner) | Slower | `pip install deeplogbot[deep]` (PyTorch) |

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enable_bot_classification` | `false` | Enable/disable bot classification step |
| `bot_classification_method` | `rules` | Classification method (`rules` or `deep`) |
| `bot_contamination` | `0.15` | Expected fraction of bot traffic (0.0-1.0) |
| `bot_provider` | `ebi` | Data provider for feature extraction |

## **Key Features**
- **Bot/Hub/Organic Classification**: Distinguishes automated bot traffic and institutional download hubs from genuine independent user downloads using DeepLogBot.
- **Optimized for High-Throughput Processing**: Uses parallel computation and efficient storage formats (Parquet).
- **Modular Execution**: Each step can be run independently or as part of the full pipeline.
- **Database Integration**: Supports structured uploads of processed metrics.
- **Customizable Parameters**: Configurable via `params.yml`.

## Usage

### Install everything
```make install```

### Clean up
```make clean```

### Uninstall everything
```make uninstall```

### Run in EBI infastructure
```./run_download_stat.sh```

For step-by-step instructions, please refer to the [usage documentation](https://pride-archive.github.io/nf-downloadstats/get_started/installation/)

## Pipeline output

To see the results of an example test run with a full size dataset refer to the [Report](https://pride-archive.github.io/nf-downloadstats/report/report-interpretation/).

# Additional documentation and tutorial

For more details, please refer to the [Complete documentation](https://pride-archive.github.io/nf-downloadstats/)

# Contributions and Support

If you would like to contribute to this pipeline, please see the [contributing guidelines](.github/CONTRIBUTING.md).

For further information or help, don't hesitate to get in touch on the Slack at EBI.
