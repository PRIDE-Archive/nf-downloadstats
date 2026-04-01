import logging
from datetime import datetime
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
    def generate_report(template_path: Path, output: Path, enable_bot_classification: bool = False,
                        total_downloads: int = 0, unique_projects: int = 0,
                        unique_users: int = 0, unique_countries: int = 0,
                        date_range: str = "") -> None:

        # Read the template HTML file
        with open(template_path, "r",
                  encoding="utf-8") as template_file:
            template_content = template_file.read()

        # Build summary section
        run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        summary_html = (
            f'<table style="width:100%; border-collapse:collapse; margin:10px 0;">'
            f'<tr><td style="padding:8px; border-bottom:1px solid #ddd;"><strong>Report Generated</strong></td>'
            f'<td style="padding:8px; border-bottom:1px solid #ddd;">{run_timestamp}</td></tr>'
            f'<tr><td style="padding:8px; border-bottom:1px solid #ddd;"><strong>Date Range</strong></td>'
            f'<td style="padding:8px; border-bottom:1px solid #ddd;">{date_range}</td></tr>'
            f'<tr><td style="padding:8px; border-bottom:1px solid #ddd;"><strong>Total Downloads</strong></td>'
            f'<td style="padding:8px; border-bottom:1px solid #ddd;">{total_downloads:,}</td></tr>'
            f'<tr><td style="padding:8px; border-bottom:1px solid #ddd;"><strong>Unique Projects</strong></td>'
            f'<td style="padding:8px; border-bottom:1px solid #ddd;">{unique_projects:,}</td></tr>'
            f'<tr><td style="padding:8px; border-bottom:1px solid #ddd;"><strong>Unique Users</strong></td>'
            f'<td style="padding:8px; border-bottom:1px solid #ddd;">{unique_users:,}</td></tr>'
            f'<tr><td style="padding:8px; border-bottom:1px solid #ddd;"><strong>Unique Countries</strong></td>'
            f'<td style="padding:8px; border-bottom:1px solid #ddd;">{unique_countries:,}</td></tr>'
            f'<tr><td style="padding:8px; border-bottom:1px solid #ddd;"><strong>Bot Classification</strong></td>'
            f'<td style="padding:8px; border-bottom:1px solid #ddd;">{"Enabled" if enable_bot_classification else "Disabled"}</td></tr>'
            f'</table>'
        )

        # Read and assign content to placeholders
        project_level_content = (
                Report.read_html_file("yearly_download.html") +
                Report.read_html_file("combined_line_chart.html") +
                Report.read_html_file("cumulative_download.html") +
                Report.read_html_file("project_downloads_histogram_1.html") +
                Report.read_html_file("top_downloaded_projects.html")
        )

        trends_content = (
            Report.read_html_file("download_over_trends.html")
        )

        maps_content = (
            Report.read_html_file("downloads_by_country.html")
        )

        user_content = (
                Report.read_html_file("unique_users_over_time.html") +
                Report.read_html_file("users_by_country.html")
        )

        bot_content = ""
        if enable_bot_classification:
            bot_content = (
                Report.read_html_file("classification_distribution.html") +
                Report.read_html_file("classification_by_year.html") +
                Report.read_html_file("organic_downloads_by_country.html")
            )

        # Replace placeholders in template
        final_report = (
            template_content
            .replace("{{project_level_content}}", project_level_content)
            .replace("{{trends_content}}", trends_content)
            .replace("{{maps_content}}", maps_content)
            .replace("{{summary_content}}", summary_html)
            .replace("{{user_content}}", user_content)
            .replace("{{bot_content}}", bot_content)
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