import plotly.express as px


class TrendsStat:

    @staticmethod
    def download_over_trends(daily_data):
        """
        Understand download trends over days, months, or years.
        """
        # Create the line chart with 'date' on the x-axis and 'count' on the y-axis
        fig = px.line(
            daily_data,
            x='date',  # X-axis: Date
            y='count',  # Y-axis: Count of downloads
            color='method',  # Group by 'method' to create separate lines
            title='File Downloads Over Time',  # Chart title
            labels={"date": "Date", "count": "Downloads", "method": "Method"}  # Axis labels
        )
        fig.write_html("download_over_trends.html")