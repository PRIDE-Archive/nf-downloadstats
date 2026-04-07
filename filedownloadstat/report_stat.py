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
    def project_stat(df: dd.DataFrame, baseurl: str) -> None:
        # --------------- 1. yearly_downloads ---------------
        yearly_downloads = df.groupby(["year", "method"]).size().reset_index()
        yearly_downloads.columns = ["year", "method", "count"]
        yearly_downloads = yearly_downloads.compute()

        yearly_totals = yearly_downloads.groupby("year", as_index=False)["count"].sum()
        yearly_totals["method"] = "Total"

        combined_data = pd.concat([yearly_downloads, yearly_totals], ignore_index=True)
        ProjectStat.yearly_download(combined_data)

        # --------------- 2. Monthly_downloads ---------------
        df_with_my = df.assign(
            month_year=df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
        )

        total_downloads = df_with_my.groupby('month_year').size().reset_index()
        total_downloads.columns = ['month_year', 'count']
        total_downloads = total_downloads.compute()
        total_downloads['method'] = 'Total'

        downloads_by_method = df_with_my.groupby(['month_year', 'method']).size().reset_index()
        downloads_by_method.columns = ['month_year', 'method', 'count']
        downloads_by_method = downloads_by_method.compute()

        unique_month_years = sorted(set(total_downloads['month_year'].unique()) |
                                     set(downloads_by_method['month_year'].unique()))

        combined_data = pd.concat([total_downloads, downloads_by_method])
        ProjectStat.combined_line_chart(combined_data, unique_month_years)

        # --------------- 3. cumulative_downloads ---------------
        total_downloads["month_year"] = pd.to_datetime(total_downloads["month_year"])
        monthly_downloads = total_downloads.sort_values("month_year")
        monthly_downloads["cumulative_count"] = monthly_downloads["count"].cumsum()
        monthly_downloads["month_year"] = monthly_downloads["month_year"].dt.strftime("%Y-%m")
        ProjectStat.cumulative_download(monthly_downloads)

        # --------------- 4.1 download count histogram ---------------
        download_counts = df.groupby("accession").size().reset_index()
        download_counts.columns = ["accession", "download_count"]
        download_counts = download_counts.compute()

        filtered_download_counts = download_counts[download_counts["download_count"] <= 10000]
        download_distribution = filtered_download_counts.groupby("download_count").size().reset_index(
            name="num_projects")
        download_distribution = download_distribution.sort_values("download_count")
        ProjectStat.project_downloads_histogram_1(download_distribution)

        # --------------- 4.2 top downloaded projects ---------------
        ProjectStat.top_downloaded_projects(download_counts, baseurl)

    @staticmethod
    def trends_stat(df: dd.DataFrame) -> None:
        daily_data = df.groupby(['date', 'method']).size().reset_index()
        daily_data.columns = ['date', 'method', 'count']
        daily_data = daily_data.compute()
        TrendsStat.download_over_trends(daily_data)

    @staticmethod
    def regional_stats(df: dd.DataFrame) -> None:
        choropleth_data = df.groupby(['country', 'year']).size().reset_index()
        choropleth_data.columns = ['country', 'year', 'count']
        choropleth_data = choropleth_data.compute()
        choropleth_data = choropleth_data.sort_values(by='year')
        RegionalStat.download_by_country(choropleth_data)

    @staticmethod
    def user_stats(df: dd.DataFrame) -> None:
        user_data = df.groupby(['date', 'year', 'month'])['user'].nunique().reset_index()
        user_data = user_data.compute()
        user_data['date'] = pd.to_datetime(user_data['date'])
        UserStat.unique_users_over_time(user_data)

        country_user_data = df.groupby(['country', 'year'])['user'].nunique().reset_index()
        country_user_data = country_user_data.compute()
        country_user_data = country_user_data.sort_values(by='year')
        UserStat.users_by_country(country_user_data)

    @staticmethod
    def bot_stats(df: dd.DataFrame) -> None:
        """Generate bot classification statistics. Requires is_bot, is_hub, is_organic columns."""
        # Derive classification in Dask using map_partitions
        def add_classification(pdf):
            pdf = pdf.copy()
            pdf['classification'] = 'organic'
            pdf.loc[pdf['is_hub'] == True, 'classification'] = 'hub'
            pdf.loc[pdf['is_bot'] == True, 'classification'] = 'bot'
            return pdf

        df_classified = df.map_partitions(add_classification)

        # 1. Overall distribution
        classification_counts = df_classified.groupby('classification').size().reset_index()
        classification_counts.columns = ['classification', 'count']
        classification_counts = classification_counts.compute()
        BotStat.classification_distribution(classification_counts)

        # 2. Classification by year
        yearly_classification = df_classified.groupby(['year', 'classification']).size().reset_index()
        yearly_classification.columns = ['year', 'classification', 'count']
        yearly_classification = yearly_classification.compute()
        BotStat.classification_by_year(yearly_classification)

        # 3. Organic downloads by country
        organic_df = df_classified[df_classified['classification'] == 'organic']
        country_organic = organic_df.groupby('country').size().reset_index()
        country_organic.columns = ['country', 'count']
        country_organic = country_organic.compute()
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

        # Only read the columns needed for reporting to reduce memory usage
        report_columns = ['date', 'year', 'month', 'user', 'accession',
                          'country', 'method']
        if enable_bot_classification:
            report_columns += ['is_bot', 'is_hub', 'is_organic']

        df = dd.read_parquet(file, columns=report_columns)

        # Filter out rows where 'year' is in skipped_years_list
        if skipped_years_list:
            df = df[~df["year"].isin(skipped_years_list)]

        logger.info("Running report generation with Dask (lazy evaluation)")

        ReportStat.project_stat(df, baseurl)
        ReportStat.trends_stat(df)
        ReportStat.regional_stats(df)
        ReportStat.user_stats(df)

        # Generate bot classification stats if the annotated columns are present
        has_bot_columns = all(col in df.columns for col in ['is_bot', 'is_hub', 'is_organic'])
        if enable_bot_classification and has_bot_columns:
            ReportStat.bot_stats(df)
            logger.info("Bot classification stats generated")
        elif enable_bot_classification:
            logger.warning("Bot classification enabled but is_bot/is_hub/is_organic columns not found in parquet")

        # Compute summary statistics using Dask (no full materialization)
        total_downloads = df.shape[0].compute()
        unique_projects = df['accession'].nunique().compute()
        unique_users = df['user'].nunique().compute()
        unique_countries = df['country'].nunique().compute()
        date_stats = df['date'].agg(['min', 'max']).compute()
        min_date = pd.to_datetime(date_stats['min']).strftime("%Y-%m-%d")
        max_date = pd.to_datetime(date_stats['max']).strftime("%Y-%m-%d")
        date_range = f"{min_date} to {max_date}"

        template_path = Path(__file__).resolve().parent.parent / "template" / report_template

        logger.info("Looking for template", extra={"template_path": str(template_path)})
        Report.generate_report(
            template_path, output,
            enable_bot_classification=enable_bot_classification,
            total_downloads=total_downloads,
            unique_projects=unique_projects,
            unique_users=unique_users,
            unique_countries=unique_countries,
            date_range=date_range,
        )

        if report_copy_filepath and Path(report_copy_filepath).is_dir():
            Report.copy_report(output, report_copy_filepath)
        else:
            logger.warning(
                "report_copy_filepath not specified or path does not exist",
                extra={"report_copy_filepath": report_copy_filepath}
            )
