import logging
from typing import Optional
import plotly.express as px
import pandas as pd

logger = logging.getLogger(__name__)


class LogFileAnalyzer:

    @staticmethod
    def log_file_size_distribution(file: str) -> None:
        """
        Visualize how file sizes are distributed, identify outliers, and determine the average or median file size.
        """
        # Load data into a DataFrame
        data = pd.read_csv(file, sep="\t", header=None, names=["file_path", "filename", "size", "lines"])

        # Create histogram of file sizes
        fig = px.histogram(data, x="size", title="File Size Distribution", labels={"size": "File Size"})
        fig.write_html("file_size_distribution.html")

    @staticmethod
    def plot_violin_for_protocols(file_list: str):
        """
        Create violin plots of file size distributions for each protocol without relying on column headers.
        """
        # Load data without headers
        data = pd.read_csv(file_list, sep="\t", header=None)

        # Assign meaningful column names
        data.columns = ["path", "filename", "size", "protocol"]

        # Create violin plot grouped by protocol
        fig = px.violin(
            data,
            y="size",
            x="protocol",
            color="protocol",
            box=True,  # Add a box plot inside the violin
            points="outliers",  # Show all data points
            title="File Size Distribution by Protocol",
            labels={"size": "File Size (Bytes)", "protocol": "Protocol Type"},
        )
        fig.write_html("file_size_violin_by_protocol.html")
        logger.info("Violin plot written", extra={"output_file": "file_size_violin_by_protocol.html"})


    @staticmethod
    def run_log_file_stat(file: str, output: str) -> None:
        """
        Run the log file statistics generation and save the visualizations in an HTML output file.
        """
        # Generate the visualizations
        LogFileAnalyzer.log_file_size_distribution(file)
        LogFileAnalyzer.plot_violin_for_protocols(file)

        # Combine the HTML files
        with open(output, "w") as f:
            f.write("<h1>Log File Statistics</h1>")

            # Embed the content of the generated HTML plots
            with open("file_size_distribution.html", "r") as dist_file:
                f.write(dist_file.read())
            with open("file_size_violin_by_protocol.html", "r") as lines_file:
                f.write(lines_file.read())
