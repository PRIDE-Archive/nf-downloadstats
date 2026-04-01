import logging
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class BotStat:

    @staticmethod
    def classification_distribution(classification_counts):
        """
        Pie chart showing overall distribution of bot, hub, and organic downloads.
        """
        fig = px.pie(
            classification_counts,
            values='count',
            names='classification',
            title='Download Classification Distribution (Bot / Hub / Organic)',
            color='classification',
            color_discrete_map={
                'bot': '#e74c3c',
                'hub': '#f39c12',
                'organic': '#2ecc71'
            }
        )
        fig.update_layout(width=900, height=500)
        fig.write_html("classification_distribution.html")

    @staticmethod
    def classification_by_year(yearly_classification):
        """
        Stacked bar chart showing classification breakdown per year.
        """
        fig = px.bar(
            yearly_classification,
            x='year',
            y='count',
            color='classification',
            title='Download Classification by Year',
            labels={"year": "Year", "count": "Downloads", "classification": "Classification"},
            barmode='stack',
            color_discrete_map={
                'bot': '#e74c3c',
                'hub': '#f39c12',
                'organic': '#2ecc71'
            }
        )
        fig.update_layout(width=1200, height=600)
        fig.write_html("classification_by_year.html")

    @staticmethod
    def organic_downloads_by_country(country_organic):
        """
        Bar chart of organic (genuine user) downloads by country.
        """
        top_countries = country_organic.nlargest(30, 'count')
        fig = px.bar(
            top_countries,
            x='country',
            y='count',
            title='Top 30 Countries by Organic (Genuine User) Downloads',
            labels={"country": "Country", "count": "Organic Downloads"},
            color='count',
            color_continuous_scale='Greens'
        )
        fig.update_layout(width=1200, height=600, xaxis_tickangle=-45)
        fig.write_html("organic_downloads_by_country.html")
