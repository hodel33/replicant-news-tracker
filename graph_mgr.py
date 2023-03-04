import plotly.offline as pyo
import plotly.express as px
import pandas as pd
import os


class GraphManager():

    def __init__(self):

        self.plot_templates = ["plotly_white", "plotly_dark", "seaborn"]
        self.plot_barmodes = ["stack", "group"]

        self.file_ext = ".html"

        # setting the directory where files will be saved to
        self.export_dir = "exports/"

        # creating a directory for our files if it doesn't exist already
        if not os.path.exists(self.export_dir):
            os.mkdir(self.export_dir)


    def plot_top_kw_graph(self, df: pd.DataFrame, top_n: int = 20):
        '''Prints an interactive graph of the top keywords and how many times they occur in the articles'''

        df = df.sort_values(by=["count"], ascending=False).head(top_n)

        # plot the bar chart using Plotly Express
        fig = px.bar(df, x="keyword", y="count", color="category")

        fig.update_layout(xaxis={"categoryorder": "total descending"}) # normally the bars would be categorized, we want a linear total view

        for template in self.plot_templates:
        
            # Customize the layout
            fig.update_layout(
                title = f"Top {top_n} Keywords - Total amount of occurences in the articles",
                xaxis_title = "Keyword",
                yaxis_title = "Count",
                legend_title="Category",
                template = template
            )
            
            # Save the chart as an HTML file
            dirname = self.export_dir
            file_ext = self.file_ext
            filename = f"top_{top_n}_keywords_graph"
            template_style = f"_{template}"
            file_path = f"{dirname}{filename}{template_style}{file_ext}"
            pyo.plot(fig, filename=file_path, auto_open=False)
            print(f"Chart saved to '{file_path}'")


    def plot_top_cat_graph(self, df: pd.DataFrame, chart_type="bar"):
        '''Prints an interactive graph of the top categories and how many times they occur in the articles'''

        df = df.sort_values(by=["count"], ascending=False)

        # Create chart based on chart_type
        if chart_type == "bar":
            fig = px.bar(df, x="category", y="count", color="category", title="Top Categories - Total amount of categorized articles",
                         labels={"category": "Category", "count": "Article Count"})

        elif chart_type == "pie":
            fig = px.pie(df, values="count", names="category", title="Top Categories - Percentage of categorized articles",
                         labels={"category": "Category", "count": "Article Count"})
            fig.update_layout(legend_title="Category")

        else:
            print("Invalid chart_type specified") # CHANGE
            return 
        
        for template in self.plot_templates:
        
            # Customize the layout
            fig.update_layout(
                template=template
            )
            
            # Save the chart as an HTML file
            dirname = self.export_dir
            file_ext = self.file_ext
            filename = f"top_categories_graph"
            template_style = f"_{template}"
            chart_style = "_bar" if chart_type == "bar" else "_pie"
            file_path = f"{dirname}{filename}{chart_style}{template_style}{file_ext}"
            pyo.plot(fig, filename=file_path, auto_open=False)
            print(f"Chart saved to '{file_path}'")


    def plot_cats_by_date_graph(self, df: pd.DataFrame):
        
        x_value = df.index

        # plot the chart using Plotly Express
        fig = px.line(df, x=x_value, y="count", color="category", markers=False,
                labels={"date": "Date (scrape date)", "count": "Article Count", "category": "Category"},
                title="Top Categories per Date (scrape date) - Total amount of categorized articles")
        
        for template in self.plot_templates:
            fig.update_layout(template = template)

            # Save the chart as an HTML file
            dirname = self.export_dir
            file_ext = self.file_ext
            filename = f"categories_by_date_graph"
            template_style = f"_{template}"
            file_path = f"{dirname}{filename}{template_style}{file_ext}"
            pyo.plot(fig, filename=file_path, auto_open=False)
            print(f"Chart saved to '{file_path}'")


    def plot_kws_by_date_graph(self, df: pd.DataFrame, kw_1: str, kw_2: str = ""):
        
        x_value = df.index

        # plot the chart using Plotly Express
        if kw_2 == "":
            fig = px.line(df, x=x_value, y=kw_1, markers=False,
                    labels={"date": "Date (scrape date)", "value": "Count", "variable": "Keyword"},
                    title="Keyword count per Date (scrape date) - Total amount of keyword occurences")
        else:
            # plot the chart using Plotly Express
            fig = px.line(df, x=x_value, y=[kw_1, kw_2], markers=False,
                    labels={"date": "Date (scrape date)", "value": "Count", "variable": "Keyword"},
                    title="Keyword count per Date (scrape date) - Total amount of keyword occurences")
        
        for template in self.plot_templates:
            fig.update_layout(template = template)

            # Save the chart as an HTML file
            dirname = self.export_dir
            file_ext = self.file_ext
            filename = f"keywords_by_date_graph"
            template_style = f"_{template}"
            file_path = f"{dirname}{filename}{template_style}{file_ext}"
            pyo.plot(fig, filename=file_path, auto_open=False)
            print(f"Chart saved to '{file_path}'")


    def plot_cats_by_domain_graph(self, df: pd.DataFrame):
        """Prints an interactive graph of article counts per category for each domain."""
        
        # Pivot the DataFrame to get categories as columns and domains as index
        #df_pivot = df.pivot(index="domain", columns="category", values="count")

        x_value = df.index

        # Create a stacked bar chart with Plotly Express
        fig = px.bar(df, x=x_value, y="count", color="category", labels={"category": "Category"})
        fig.update_layout(title="Top Categories per Domain - Total amount of categorized articles",
                      xaxis_title="Categories per Domain",
                      yaxis_title="Article Count")
        
        for barmode in self.plot_barmodes:
            for template in self.plot_templates:
            
                # Customize the layout
                fig.update_layout(
                    barmode=barmode,
                    template=template
                )
                
                # Save the chart as an HTML file
                dirname = self.export_dir
                file_ext = self.file_ext
                filename = "categories_by_domain_graph"
                barmode_style = f"_{barmode}"
                template_style = f"_{template}"
                file_path = f"{dirname}{filename}{barmode_style}{template_style}{file_ext}"
                pyo.plot(fig, filename=file_path, auto_open=False)
                print(f"Chart saved to '{file_path}'")


    def plot_country_mentions_heatmap(self, df: pd.DataFrame):
        """Prints an interactive heatmap of the world showing the number of times each country has been mentioned in the articles."""

        fig = px.choropleth(df, locations="iso3_country_code", color="count", color_continuous_scale="Reds",
                            title="Top Countries - Number of times each country has been mentioned in the articles",
                            projection="natural earth", hover_name = "country", labels={"count": "Count"})
        
        fig.update_geos(showcoastlines=True, coastlinecolor="Black",
                        showland=True, landcolor="LightGray",
                        showocean=True, oceancolor="LightBlue")
        
        fig = fig.update_traces(marker_line_width=0.2, hovertemplate="<b>%{z}</b> | %{location}")

        fig.update_layout(showlegend=True)

        # Save the chart as an HTML file
        dirname = self.export_dir
        file_ext = self.file_ext
        filename = "country_mentions_heatmap"
        geo_proj_style = f"_natural_earth"
        file_path = f"{dirname}{filename}{geo_proj_style}{file_ext}"
        pyo.plot(fig, filename=file_path, auto_open=False)
        print(f"Heatmap saved to '{file_path}'")