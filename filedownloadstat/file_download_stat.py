import os

from stattypes.project_stat import ProjectStat
from stattypes.regional_stat import RegionalStat
from stattypes.trends_stat import TrendsStat
from stattypes.user_stat import UserStat
from report import Report
import pandas as pd


class FileDownloadStat:

    @staticmethod
    def project_stat(df: pd.DataFrame):
        # --------------- 1. yearly_downloads ---------------
        # Group data by year and method, count occurrences
        yearly_downloads = df.groupby(["year", "method"]).size().reset_index(name="count")
        ProjectStat.yearly_download(yearly_downloads)

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
        # Count number of downloads per project (group by "accession")
        download_counts = df.groupby("accession").size().reset_index(name="download_count")
        filtered_download_counts = download_counts[download_counts["download_count"] <= 10000]
        ProjectStat.project_downloads_histogram_1(filtered_download_counts)
        # --------------- 4.2 download count histogram ---------------
        # Count number of downloads per project (group by "accession")
        download_counts = df.groupby("accession").size().reset_index(name="download_count")
        filtered_download_counts = download_counts[download_counts["download_count"] <= 20000]
        filtered_download_counts = filtered_download_counts[download_counts["download_count"] > 10000]
        ProjectStat.project_downloads_histogram_2(filtered_download_counts)

    @staticmethod
    def trends_stat(df: pd.DataFrame):
        # Group data by date and count the occurrences
        # Group by date and method to sum the count of downloads per method per day
        # Group by 'date' and 'method' and count the occurrences of each combination
        daily_data = df.groupby(['date', 'method'], as_index=False).size().rename(columns={'size': 'count'})
        TrendsStat.download_over_treands(daily_data)

    @staticmethod
    def regional_stats(df: pd.DataFrame):
        # Group data by country to get the count of downloads
        choropleth_data = df.groupby(['country', 'year']).size().reset_index(name='count')
        choropleth_data = choropleth_data.sort_values(by='year')
        RegionalStat.download_by_country(choropleth_data)

    @staticmethod
    def user_stats(df: pd.DataFrame):
        # Calculate unique users per date
        user_data = df.groupby(['date', 'year', 'month'], as_index=False)['user'].nunique()
        user_data['date'] = pd.to_datetime(user_data['date'], unit='ms')  # Convert date to datetime
        UserStat.unique_users_over_time(user_data)

        # Calculate unique users per country
        country_user_data = df.groupby(['country', 'year'], as_index=False)['user'].nunique()
        country_user_data = country_user_data.sort_values(by='year')
        UserStat.users_by_country(country_user_data)

    @staticmethod
    def run_file_download_stat(file, output):
        """
        Run the log file statistics generation and save the visualizations in an HTML output file.
        """

        # Load the Parquet file
        data = pd.read_json(file)
        # Convert to DataFrame
        df = pd.DataFrame(data)

        FileDownloadStat.project_stat(df)
        FileDownloadStat.trends_stat(df)
        FileDownloadStat.regional_stats(df)
        FileDownloadStat.user_stats(df)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, "..", "template", "pride_report.html")

        # Normalize path for cross-platform compatibility
        template_path = os.path.normpath(template_path)

        print(f"Looking for template at: {template_path}")
        Report.generate_report(template_path, output)




