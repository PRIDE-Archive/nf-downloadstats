import logging
from pathlib import Path
from typing import Optional

from interfaces import IReportGenerator

logger = logging.getLogger(__name__)


class Report(IReportGenerator):

    # Function to read HTML content from a file
    @staticmethod
    def read_html_file(file_path: Path) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            return f"<p>Missing content: {file_path}</p>"

    @staticmethod
    def generate_report(template_path: Path, output: Path) -> None:

        # Read the template HTML file
        with open(template_path, "r",
                  encoding="utf-8") as template_file:
            template_content = template_file.read()

        # Read and assign content to placeholders
        project_level_content = (
                Report.read_html_file("yearly_download.html") +
                Report.read_html_file("combined_line_chart.html") +
                Report.read_html_file("cumulative_download.html") +
                Report.read_html_file("project_downloads_histogram_1.html") +
                Report.read_html_file("top_downloaded_projects.html")
        )

        trends_content = (
            Report.read_html_file("download_over_treands.html")  # Correct the filename if needed
        )

        maps_content = (
            Report.read_html_file("downloads_by_country.html")
        )

        user_content = (
                Report.read_html_file("unique_users_over_time.html") +
                Report.read_html_file("users_by_country.html")
        )

        # Replace placeholders in template
        final_report = (
            template_content
            .replace("{{project_level_content}}", project_level_content)
            .replace("{{trends_content}}", trends_content)
            .replace("{{maps_content}}", maps_content)
            .replace("{{user_content}}", user_content)
        )

        # Write the final HTML report
        with open(output, "w", encoding="utf-8") as output_file:
            output_file.write(final_report)

        logger.info("Report generated successfully", extra={"output": output})

    @staticmethod
    def copy_report(output: Path, report_copy_filepath: Path) -> None:
        """
        Open the original file to read and the new file to write
        """
        file_copy = Path(report_copy_filepath) / "file_download_stat_local.html"
        with open(output, "r") as original_file, open(file_copy, "w") as new_file:
            for line in original_file:
                new_file.write(line)

        logger.info("File copied successfully", extra={"source": output, "destination": str(file_copy)})