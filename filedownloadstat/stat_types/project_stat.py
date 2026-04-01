import plotly.express as px


class ProjectStat:
    """
    Project Level stat
    """

    @staticmethod
    def combined_line_chart(combined_data: 'pd.DataFrame', unique_month_years: list) -> None:
        """
        Highlight number of monthly downloads
        """
        # Plot: Combined line chart
        fig = px.line(
            combined_data,
            x='month_year',
            y='count',
            color='method',
            title='Monthly Downloads: Total and by Method',
            labels={'month_year': 'Month-Year', 'count': 'Downloads', 'method': 'Download Method'}
        )
        # Update layout for fixed x-axis ticks
        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=unique_month_years,
                ticktext=unique_month_years
            ),
            xaxis_tickangle=-45
        )
        # Update layout for smoother animation
        # fig.update_layout(transition={'duration': 500}, xaxis_tickangle=-45)

        fig.write_html('combined_line_chart.html')

    @staticmethod
    def yearly_download(yearly_downloads: 'pd.DataFrame') -> None:
        """
        Create a bar chart with year on X-axis, count on Y-axis, and method as color
        """
        # Ensure year is treated as a categorical variable
        yearly_downloads["year"] = yearly_downloads["year"].astype(str)

        fig = px.bar(
            yearly_downloads,
            x="year",
            y="count",
            color="method",
            barmode="group",  # Group bars by method
            title="Yearly Total Downloads Separated by Method (Including Totals)",
            labels={"count": "Downloads", "year": "Year", "method": "Download Method"}
        )
        fig.write_html('yearly_download.html')

    @staticmethod
    def cumulative_download(monthly_downloads: 'pd.DataFrame') -> None:
        # Create line chart
        fig = px.line(
            monthly_downloads,
            x="month_year",
            y="cumulative_count",
            title="Cumulative Downloads Over Time (Month-Year)",
            labels={"month_year": "Month-Year", "cumulative_count": "Cumulative Downloads"},
            markers=True  # Adds markers to show data points clearly
        )
        fig.write_html('cumulative_download.html')

    @staticmethod
    def project_downloads_histogram_1(download_counts: 'pd.DataFrame') -> None:
        """
        This will create a histogram where each bar represents how many projects fall into different download count ranges
        """
        fig = px.line(
            download_counts,
            x="download_count",
            y="num_projects",
            title="Distribution of Projects by Download Count",
            labels={"download_count": "Number of Downloads", "num_projects": "Number of Projects"},
            markers=True  # Add markers to highlight points
        )
        # Update layout to ensure x-axis starts at 0 and remove negative scale
        fig.update_layout(
            xaxis=dict(range=[0, None])  # Start at 0, let Plotly determine the max
        )
        fig.write_html('project_downloads_histogram_1.html')

    @staticmethod
    def top_downloaded_projects(df: 'pd.DataFrame', baseurl: str) -> None:
        """
        This will create a horizontal bar chart with Top 10 Most Downloaded Projects
        """

        df["accession_url"] = df["accession"].apply(
            lambda x: f'<a href="{baseurl}{x}" target="_blank">{x}</a>')

        # top_n_options = [5, 10, 15]
        #
        # Create initial figure (default to Top 10)
        initial_top_n = 10
        filtered_df = df.nlargest(initial_top_n, "download_count")

        fig = px.bar(
            filtered_df,
            x="download_count",
            y="accession_url",  # Use the clickable version
            orientation="h",
            title="Top Downloaded Projects",
            labels={"download_count": "Number of Downloads", "accession_url": "Project Accession"},
            text="download_count"
        )

        fig.write_html('top_downloaded_projects.html')
