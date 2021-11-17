from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import NumeralTickFormatter
import numpy as np
import casparser
import pandas as pd


def util(filename, password):
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
    script_code, chart_code = components(chart)
    return script_code, chart_code


def getChart(df):
    p = figure(title="Investment", x_axis_label='Date',
               y_axis_label='Value (INR)', x_axis_type='datetime',
               y_axis_type='linear', plot_width=900, plot_height=500,
               tools='pan,box_zoom,reset', toolbar_location='right')

    date = np.array(df.index, dtype=np.datetime64)
    p.yaxis[0].formatter = NumeralTickFormatter(format='0f')

    p.line(date, df.investment, legend_label='Investment',
           color='#4bcf3a', muted_alpha=0.2, line_width=2)

    p.legend.location = "top_left"
    p.legend.click_policy = "mute"

    return p
