# Standard modules
import os
import pandas as pd
from tqdm import tqdm
import itertools

# Third-party modules -> requirements.txt
import plotly.express as px
import plotly.offline as pyo


class GraphManager():

    def __init__(self):

        # adding a couple of chart templates & barmodes to some of the charts which gives the users more viewing options
        self.plot_templates = ["plotly_white", "plotly_dark", "seaborn"]
        self.plot_barmodes = ["stack", "group"]

        self.file_ext = ".html"

        # setting the directory where files will be saved to
        self.export_dir = "exports/"

        # creating a directory for our files if it doesn't exist already
        if not os.path.exists(self.export_dir):
            os.mkdir(self.export_dir)

        # custom tqdm loading bar format
        self.custom_bar = "    [{bar:30}] {percentage:3.0f}%  "
        tqdm.pandas(bar_format=self.custom_bar, ascii=" =", leave=False)


    def plot_top_kw_graph(self, df: pd.DataFrame, top_n: int = 20) -> list:
        '''Prints an interactive graph of the top keywords and how many times they occur in the articles'''

        df = df.sort_values(by=["count"], ascending=False).head(top_n)

        # plot the bar chart using Plotly Express
        fig = px.bar(df, x="keyword", y="count", color="category")
        fig.update_layout(xaxis={"categoryorder": "total descending"}) # normally the bars would be categorized, we want a linear total view

        saved_files = []

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
            saved_files.append(f"Chart saved to '{file_path}'")

        return saved_files


    def plot_top_cat_graph(self, df: pd.DataFrame, chart_type="bar") -> list:
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
        
        saved_files = []
        
        # Calculate the total number of exports for tqdm
        tot_exports = len(self.plot_templates) * len(["bar", "pie"])

        # Wrap the loop with tqdm
        for template in tqdm(self.plot_templates, total=tot_exports, bar_format=self.custom_bar, ascii=" =", leave=False):

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
            saved_files.append(f"Chart saved to '{file_path}'")

        return saved_files


    def plot_cats_by_date_graph(self, df: pd.DataFrame) -> list:
        '''Prints an interactive graph of the total amount of categorized articles by date'''
        
        x_value = df.index

        # plot the chart using Plotly Express
        fig = px.scatter(df, x=x_value, y="count", color="category", 
                labels={"date": "Date (scrape date)", "count": "Article Count", "category": "Category"},
                title="Top Categories per Date (scrape date) - Total amount of categorized articles")
        
        saved_files = []

        # Calculate the total number of exports for tqdm
        tot_exports = len(self.plot_templates)

        # Wrap the loop with tqdm
        for template in tqdm(self.plot_templates, total=tot_exports, bar_format=self.custom_bar, ascii=" =", leave=False):

            fig.update_layout(template = template)

            # Save the chart as an HTML file
            dirname = self.export_dir
            file_ext = self.file_ext
            filename = f"categories_by_date_graph"
            template_style = f"_{template}"
            file_path = f"{dirname}{filename}{template_style}{file_ext}"
            pyo.plot(fig, filename=file_path, auto_open=False)
            saved_files.append(f"Chart saved to '{file_path}'")

        return saved_files


    def plot_kws_by_date_graph(self, df: pd.DataFrame, kw_1: str, kw_2: str = "") -> list:
        '''Prints an interactive graph of the user specidic keyword(s) and how many times it/they occur in the articles by date'''

        x_value = df.index

        # plot the chart using Plotly Express
        if kw_2 == "": # in case only 1 keyword is used

            fig = px.scatter(df, x=x_value, y=kw_1, 
                    labels={"date": "Date (scrape date)", kw_1: "Count"},
                    title="Keyword count per Date (scrape date) - Total amount of keyword occurences")
            # overriding Plotly variables since single traced plots won't have a legend visible as default
            fig["data"][0]["showlegend"]=True
            fig["data"][0]["name"] = kw_1

        else:

            fig = px.scatter(df, x=x_value, y=[kw_1, kw_2], 
                    labels={"date": "Date (scrape date)", "value": "Count"},
                    title="Keyword count per Date (scrape date) - Total amount of keyword occurences")
            
        saved_files = []

        # Calculate the total number of exports for tqdm
        tot_exports = len(self.plot_templates)

        # Wrap the loop with tqdm
        for template in tqdm(self.plot_templates, total=tot_exports, bar_format=self.custom_bar, ascii=" =", leave=False):
        
            fig.update_layout(template=template, legend_title="Keyword")

            # Save the chart as an HTML file
            dirname = self.export_dir
            file_ext = self.file_ext
            filename = f"custom_keyword_by_date_graph"
            template_style = f"_{template}"
            file_path = f"{dirname}{filename}{template_style}{file_ext}"
            pyo.plot(fig, filename=file_path, auto_open=False)
            saved_files.append(f"Chart saved to '{file_path}'")

        return saved_files


    def plot_cats_by_domain_graph(self, df: pd.DataFrame) -> list:
        """Prints an interactive graph of article counts per category for each domain."""
  
        x_value = df.index

        # Create a stacked bar chart with Plotly Express
        fig = px.bar(df, x=x_value, y="count", color="category", labels={"category": "Category"})
        fig.update_layout(title="Top Categories per Domain - Total amount of categorized articles",
                    xaxis_title="Categories per Domain",
                    yaxis_title="Article Count")
        
        saved_files = []

        # Calculate the total number of exports for tqdm
        tot_exports = len(self.plot_barmodes) * len(self.plot_templates)
        
        # Wrap the outer loop with tqdm
        for barmode, template in tqdm(itertools.product(self.plot_barmodes, self.plot_templates), total=tot_exports, bar_format=self.custom_bar, ascii=" =", leave=False):
            
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
            saved_files.append(f"Chart saved to '{file_path}'")

        return saved_files


    def plot_country_mentions_heatmap(self, df: pd.DataFrame) -> list:
        """Prints an interactive heatmap of the world showing the number of times each country has been mentioned in the articles."""

        saved_files = []

        # plot the heatmap using Plotly Express
        fig = px.choropleth(df, locations="iso3_country_code", color="count", color_continuous_scale="Reds",
                            title="Top Countries - Number of times each country has been mentioned in the articles",
                            projection="natural earth", hover_name = "country", labels={"count": "Count"})
        
        # Customize the layout
        fig.update_geos(showcoastlines=True, coastlinecolor="Black",
                        showland=True, landcolor="LightGray",
                        showocean=True, oceancolor="LightBlue",
                        showlakes=True, lakecolor="LightBlue",
                        showrivers=True, rivercolor="LightBlue")
        
        fig = fig.update_traces(marker_line_width=0.2, hovertemplate="<b>%{z}</b> | %{location}")

        saved_files = []

        # Calculate the total number of exports for tqdm
        tot_exports = len(self.plot_templates)

        # Wrap the loop with tqdm
        for template in tqdm(self.plot_templates, total=tot_exports, bar_format=self.custom_bar, ascii=" =", leave=False):

            fig.update_layout(showlegend=True, template=template)

            # Save the chart as an HTML file
            dirname = self.export_dir
            file_ext = self.file_ext
            filename = "country_mentions_heatmap"
            geo_proj_style = f"_natural_earth"
            template_style = f"_{template}"
            file_path = f"{dirname}{filename}{geo_proj_style}{template_style}{file_ext}"
            pyo.plot(fig, filename=file_path, auto_open=False)
            saved_files.append(f"Chart saved to '{file_path}'")

        return saved_files