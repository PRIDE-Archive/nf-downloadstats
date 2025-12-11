import logging
import plotly.express as px

logger = logging.getLogger(__name__)


class RegionalStat:

    @staticmethod
    def download_by_country(choropleth_data):
        """
         Visualize downloads geographically
        """
        # Plot Bubble Map with animation_frame
        fig = px.scatter_geo(
            choropleth_data,
            locations='country',
            locationmode='country names',
            size='count',  # Size of the bubbles
            color='count',  # Color scale based on count
            hover_name='country',  # Country name on hover
            animation_frame='year',  # Animation by year
            title='Downloads by Country Over Time',
            labels={'count': 'Downloads', 'country': 'Country'},
            size_max=50,
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        # Update layout to show the latest year by default
        latest_year = choropleth_data['year'].max()
        if fig.layout.updatemenus and len(fig.layout.updatemenus) > 0:
            if fig.layout.updatemenus[0].buttons and len(fig.layout.updatemenus[0].buttons) > 0:
                fig.layout.updatemenus[0].buttons[-1].args[1]['frame']['redraw'] = True  # Force redraw
            else:
                logger.warning("No buttons in updatemenus")
        else:
            logger.warning("No updatemenus present")

        fig.update_layout(
            geo=dict(
                showcoastlines=True,
                projection_type='natural earth'
            ),
            sliders=[
                dict(
                    steps=[
                        dict(
                            args=[[year], {"frame": {"duration": 500, "redraw": True}}],
                            label=str(year),
                            method="animate"
                        )
                        for year in sorted(choropleth_data['year'].unique())
                    ],
                    active=sorted(choropleth_data['year'].unique()).index(latest_year),
                    currentvalue=dict(font=dict(size=14), prefix="Year: ", visible=True),
                    pad=dict(t=50),
                )
            ]
        )
        fig.update_layout(width=1200, height=800)
        fig.write_html("downloads_by_country.html")
