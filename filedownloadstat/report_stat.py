import logging
from pathlib import Path
from typing import List, Optional

from stat_types import ProjectStat, RegionalStat, TrendsStat, UserStat, BotStat
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
        user_data['date'] = pd.to_datetime(user_data['date'])

        UserStat.unique_users_over_time(user_data)

        # Calculate unique users per country
        country_user_data = df.groupby(['country', 'year'], as_index=False)['user'].nunique()
        country_user_data = country_user_data.sort_values(by='year')
        UserStat.users_by_country(country_user_data)

    @staticmethod
    def bot_stats(df: pd.DataFrame) -> None:
        """Generate bot classification statistics. Requires is_bot, is_hub, is_organic columns."""
        # Derive classification label from boolean columns
        def get_classification(row):
            if row.get('is_bot', False):
                return 'bot'
            elif row.get('is_hub', False):
                return 'hub'
            else:
                return 'organic'

        df = df.copy()
        df['classification'] = df.apply(get_classification, axis=1)

        # 1. Overall distribution
        classification_counts = df.groupby('classification').size().reset_index(name='count')
        BotStat.classification_distribution(classification_counts)

        # 2. Classification by year
        yearly_classification = df.groupby(['year', 'classification']).size().reset_index(name='count')
        BotStat.classification_by_year(yearly_classification)

        # 3. Organic downloads by country
        organic_df = df[df['classification'] == 'organic']
        country_organic = organic_df.groupby('country').size().reset_index(name='count')
        country_organic = country_organic.sort_values('count', ascending=False)
        BotStat.organic_downloads_by_country(country_organic)

    @staticmethod
    def run_file_download_stat(
        file: str,
        output: str,
        report_template: str,
        baseurl: str,
        report_copy_filepath: Optional[str],
        skipped_years_list: List[int],
        enable_bot_classification: bool = False
    ) -> None:
        """
        Run the log file statistics generation and save the visualizations in an HTML output file.
        """
        logger.info("Loading data from Parquet", extra={"file": file})

        df = dd.read_parquet(file)

        # Filter out rows where 'year' is in skipped_years_list
        if skipped_years_list:
            df = df[~df["year"].isin(skipped_years_list)]

        df_pandas = df.compute()
        logger.debug("Parquet data loaded", extra={"file": file, "row_count": len(df_pandas)})

        # Convert 'date' to Pandas datetime format
        df_pandas['date'] = pd.to_datetime(df_pandas['date'])

        ReportStat.project_stat(df_pandas, baseurl)
        ReportStat.trends_stat(df_pandas)
        ReportStat.regional_stats(df_pandas)
        ReportStat.user_stats(df_pandas)

        # Generate bot classification stats if the annotated columns are present
        has_bot_columns = all(col in df_pandas.columns for col in ['is_bot', 'is_hub', 'is_organic'])
        if enable_bot_classification and has_bot_columns:
            ReportStat.bot_stats(df_pandas)
            logger.info("Bot classification stats generated")
        elif enable_bot_classification:
            logger.warning("Bot classification enabled but is_bot/is_hub/is_organic columns not found in parquet")

        template_path = Path(__file__).resolve().parent.parent / "template" / report_template

        logger.info("Looking for template", extra={"template_path": str(template_path)})
        Report.generate_report(template_path, output, enable_bot_classification=enable_bot_classification)

        if report_copy_filepath and Path(report_copy_filepath).is_dir():
            Report.copy_report(output, report_copy_filepath)
        else:
            logger.warning(
                "report_copy_filepath not specified or path does not exist",
                extra={"report_copy_filepath": report_copy_filepath}
            )
