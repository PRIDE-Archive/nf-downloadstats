import logging
from pathlib import Path
from typing import List, Optional

from stat_types import ProjectStat, RegionalStat, TrendsStat, UserStat
from report_util import Report
import pandas as pd
import dask.dataframe as dd

logger = logging.getLogger(__name__)

class ReportStat:

    @staticmethod
    def project_stat(df: pd.DataFrame, baseurl: str) -> None:
        # --------------- 1. yearly_downloads ---------------
        # Group data by year and method, count occurrences
        yearly_downloads = df.groupby(["year", "method"]).size().reset_index(name="count")
        yearly_totals = yearly_downloads.groupby("year", as_index=False)["count"].sum()
        yearly_totals["method"] = "Total"  # Add a 'Total' label for the method

        # Combine the original data with the totals
        combined_data = pd.concat([yearly_downloads, yearly_totals], ignore_index=True)
        ProjectStat.yearly_download(combined_data)

        # --------------- 2. Monthly_downloads ---------------
        # Add a `month_year` column
        df['month_year'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)

        # Ensure the x-axis displays all `month_year` values
        unique_month_years = sorted(df['month_year'].unique())

        # Total downloads per month-year
        total_downloads = df.groupby('month_year').size().reset_index(name='count')
        total_downloads['method'] = 'Total'  # Label for the total count

        # Downloads per month-year by method
        downloads_by_method = df.groupby(['month_year', 'method']).size().reset_index(name='count')

        # Combine total downloads and method-specific downloads
        combined_data = pd.concat([total_downloads, downloads_by_method])

        ProjectStat.combined_line_chart(combined_data, unique_month_years)

        # --------------- 3. cumulative_downloads ---------------

        # Sort by date to ensure proper cumulative calculation
        total_downloads["month_year"] = pd.to_datetime(total_downloads["month_year"])
        monthly_downloads = total_downloads.sort_values("month_year")

        # Calculate cumulative sum
        monthly_downloads["cumulative_count"] = monthly_downloads["count"].cumsum()

        # Convert back to string format for plotting
        monthly_downloads["month_year"] = monthly_downloads["month_year"].dt.strftime("%Y-%m")
        ProjectStat.cumulative_download(monthly_downloads)

        # --------------- 4.1 download count histogram ---------------

        # Group by accession and count downloads
        download_counts = df.groupby("accession").size().reset_index(name="download_count")

        # Filter download counts (only <= 10,000)
        filtered_download_counts = download_counts[download_counts["download_count"] <= 10000]

        # Aggregate to get the number of projects for each download count
        download_distribution = filtered_download_counts.groupby("download_count").size().reset_index(
            name="num_projects")

        # Sort data to ensure proper line chart visualization
        download_distribution = download_distribution.sort_values("download_count")
        ProjectStat.project_downloads_histogram_1(download_distribution)

        # # --------------- 4.2 download count histogram ---------------

        # # Group by accession and count downloads
        download_counts = df.groupby("accession").size().reset_index(name="download_count")
        ProjectStat.top_downloaded_projects(download_counts, baseurl)

    @staticmethod
    def trends_stat(df: pd.DataFrame) -> None:
        # Group data by date and count the occurrences
        # Group by date and method to sum the count of downloads per method per day
        # Group by 'date' and 'method' and count the occurrences of each combination
        daily_data = df.groupby(['date', 'method'], as_index=False).size().rename(columns={'size': 'count'})
        TrendsStat.download_over_trends(daily_data)

    @staticmethod
    def regional_stats(df: pd.DataFrame) -> None:
        # Group data by country to get the count of downloads
        choropleth_data = df.groupby(['country', 'year']).size().reset_index(name='count')
        choropleth_data = choropleth_data.sort_values(by='year')
        RegionalStat.download_by_country(choropleth_data)

    @staticmethod
    def user_stats(df: pd.DataFrame) -> None:
        # Calculate unique users per date
        user_data = df.groupby(['date', 'year', 'month'], as_index=False)['user'].nunique()
        user_data['date'] = pd.to_datetime(user_data['date'], unit='ms')  # Convert date to datetime
        # user_data['date'] = pd.to_datetime(user_data['date'], format='%Y-%m-%d')  # Use the correct format

        UserStat.unique_users_over_time(user_data)

        # Calculate unique users per country
        country_user_data = df.groupby(['country', 'year'], as_index=False)['user'].nunique()
        country_user_data = country_user_data.sort_values(by='year')
        UserStat.users_by_country(country_user_data)

    @staticmethod
    def run_file_download_stat(
        file: str,
        output: str,
        report_template: str,
        baseurl: str,
        report_copy_filepath: Optional[str],
        skipped_years_list: List[int]
    ) -> None:
        """
        Run the log file statistics generation and save the visualizations in an HTML output file.
        """
        logger.info("Loading data from Parquet", extra={"file": file})

        df = dd.read_parquet(file)
        df_computed = df.compute()
        logger.debug("Parquet data preview", extra={"file": file, "row_count": len(df_computed)})
        
        # Filter out rows where 'year' is in skipped_years_list
        df = df[~df["year"].isin(skipped_years_list)]
        df_pandas = df.compute()

        # Convert 'date' to Pandas datetime format
        df_pandas['date'] = pd.to_datetime(df_pandas['date'])

        ReportStat.project_stat(df_pandas, baseurl)
        ReportStat.trends_stat(df_pandas)
        ReportStat.regional_stats(df_pandas)
        ReportStat.user_stats(df_pandas)

        template_path = Path(__file__).resolve().parent.parent / "template" / report_template

        logger.info("Looking for template", extra={"template_path": str(template_path)})
        Report.generate_report(template_path, output)

        if report_copy_filepath and Path(report_copy_filepath).is_dir():
            Report.copy_report(output, report_copy_filepath)
        else:
            logger.warning(
                "report_copy_filepath not specified or path does not exist",
                extra={"report_copy_filepath": report_copy_filepath}
            )
