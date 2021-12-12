import numpy as np
import casparser
import pandas as pd
from math import pi

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import NumeralTickFormatter
from bokeh.palettes import Category20c, Viridis, YlGn
from bokeh.transform import cumsum


def util(filename, password, userData):
    data = casparser.read_cas_pdf(filename, password, output="csv")
    f = open("temp.csv", "w")
    f.write(data)
    f.close()
    df = pd.read_csv('temp.csv', index_col=['date'])
    df = df.sort_index()
    df = df[['type', 'amount', 'units', 'nav', 'balance', 'scheme', 'amfi']].loc[(
        df.type == 'PURCHASE') | (df.type == 'REDEMPTION')]
    df['investment'] = df.amount.cumsum()
    chart = getChart(df)
    pie = getPieChart(userData=userData)
    script_code, chart_codes = components((chart, pie))
    return script_code, chart_codes


def getChart(df):
    p = figure(title="Investment", x_axis_label='Date',
               y_axis_label='Value (INR)', x_axis_type='datetime',
               y_axis_type='linear', plot_width=800, plot_height=450,
               tools='pan,box_zoom,reset', toolbar_location='right')

    date = np.array(df.index, dtype=np.datetime64)
    p.yaxis[0].formatter = NumeralTickFormatter(format='0f')

    p.line(date, df.investment, legend_label='Investment',
           color='#4bcf3a', muted_alpha=0.2, line_width=2)

    p.legend.location = "top_left"
    p.legend.click_policy = "mute"

    return p


def getPieChart(userData):
    x = {fund['scheme']: fund['current'] for fund in userData}

    data = pd.Series(x).reset_index(
        name='current').rename(columns={'index': 'scheme'})
    data['angle'] = data['current']/data['current'].sum() * 2*pi
    data['color'] = YlGn[len(x)]

    p = figure(plot_width=800, plot_height=550, title="Fund Distribution", toolbar_location=None,
               tools="hover", tooltips="@scheme: ₹@current", x_range=(-0.5, 1.0))

    p.wedge(x=0, y=1, radius=0.4,
            start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_color="white", fill_color='color', legend_field='scheme', source=data)

    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    return p
