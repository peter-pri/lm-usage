# Plot an Interactive Candlestick Chart in a Browser
#
# Copyright 2021 Peter Prisille. See LICENSE file for details.
#
#
# todo: global variables shall not be used with dash callbacks -> rework the code
#       see https://dash.plotly.com/sharing-data-between-callbacks


import requests
import json
import arrow
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from datetime import datetime
from datetime import timedelta
import datetime
import time
import logging

logging.basicConfig(
    format='%(asctime)s,%(msecs)-6.1f [%(process)d]%(funcName)s# %(message)s',
    datefmt='%H:%M:%S')
log = logging.getLogger()
log.setLevel(logging.INFO)  # 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'

colors = {
    'background': '#F0F0F0',
    'text': '#7FDBFF'
}

off_button_style = {'backgroundColor': 'white',
                    'color': 'black',
                    'height': '50px',
                    'width': '180px',
                    'marginTop': '50px',
                    'marginLeft': '50px',
                    'borderRadius': '15px',
                    'border': 'solid',
                    'fontSize': '21px',
                    'margin': '10px 10px'}

on_button_style = {'backgroundColor': 'grey',
                   'color': 'white',
                   'height': '50px',
                   'width': '180px',
                   'marginTop': '50px',
                   'marginLeft': '50px',
                   'borderRadius': '15px',
                   'border': 'solid',
                   'fontSize': '21px',
                   'margin': '10px 10px'}

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
style_sheet = ['./style_sheet.css']  # derived from stylesheet above

app = dash.Dash(__name__, external_stylesheets=style_sheet)

mic = "XMUN"

TOKEN_KEY = "insert_your_token_here"  # please adapt to your token !

authorization = f"Bearer {TOKEN_KEY}"

isin = ""

next_link = ""
previous_link = ""
link_to_lm = ""

button_previous_cnt = 0
button_next_cnt = 0

n_timer_cnt = 0

button_live_cnt = 0
button_day_cnt = 0
button_week_cnt = 0
button_month_cnt = 0
button_4_months_cnt = 0
button_year_cnt = 0
button_5_years_cnt = 0
button_all_cnt = 0

button_color_live = off_button_style
button_color_day = off_button_style
button_color_week = off_button_style
button_color_month = off_button_style
button_color_4_months = off_button_style
button_color_year = off_button_style
button_color_5_years = off_button_style
button_color_all = off_button_style

radio_buttons = ("Live", "1 Day", "1 Week", "1 Month", "4 Months", "1 Year", "5 Years", "All Time")
radio_button_state = radio_buttons.index("1 Week")

time_step_selection = ("Minute", "Hour", "Day")
time_step_state = time_step_selection.index("Hour")

link_to_lm_until_datetime = datetime.datetime.today()  # just define type of variable
link_to_lm_from_datetime = datetime.datetime.today()  # just define type of variable

# todo: should be 7 days
NEARLY_7_DAYS = timedelta(days=6) + timedelta(hours=23) + timedelta(minutes=59) + timedelta(seconds=59)
# todo: should be 31 days
NEARLY_31_DAYS = timedelta(days=30) + timedelta(hours=23) + timedelta(minutes=59) + timedelta(seconds=59)

time_frame = NEARLY_7_DAYS
time_frame_all = NEARLY_7_DAYS

TIMER_INTERVAL = 30 * 1000  # in milliseconds = 30s
TIMER_INTERVAL_LONG = 60 * 60 * 1000  # in milliseconds = 1 hour


def retrieve_data(link_to_lm_lc):
    request = requests.get(link_to_lm_lc, headers={"Authorization": authorization})
    # example answer:
    # "next": "https://paper.lemon.markets/rest/v1/trading-venues/XMUN/instruments/US67066G1040/data/ohlc/h1/?date_until=1627221990.191188&date_from=1624557795.095594",
    # "previous": "https://paper.lemon.markets/rest/v1/trading-venues/XMUN/instruments/US67066G1040/data/ohlc/h1/?date_until=1621893600.0&date_from=1619229404.904406",

    log.debug(request)
    df = pd.DataFrame()
    parsed = json.loads(request.content)
    if str(request) != "<Response [200]>":
        log.error(json.dumps(parsed, indent=4, sort_keys=True))
        next_link_lc = None
        previous_link_lc = None
    else:
        # everything ok:
        log.debug(json.dumps(parsed, indent=4, sort_keys=True))
        next_link_lc = parsed['next']
        previous_link_lc = parsed['previous']
        log.info(next_link_lc)
        log.info(previous_link_lc)

        length = len(parsed['results'])

        column_names = ["Date", "Open", "High", "Low", "Close", "Volume"]
        df = pd.DataFrame(columns=column_names, index=range(length))

        for i in range(len(parsed['results'])):
            df.loc[length - 1 - i]["Date"] = arrow.get(parsed['results'][i]['t']).to('local').datetime
            df.loc[length - 1 - i]["Open"] = parsed['results'][i]['o']
            df.loc[length - 1 - i]["High"] = parsed['results'][i]['h']
            df.loc[length - 1 - i]["Low"] = parsed['results'][i]['l']
            df.loc[length - 1 - i]["Close"] = parsed['results'][i]['c']
            df.loc[length - 1 - i]["Volume"] = 0

        df.Date = pd.to_datetime(df.Date)
        df.Open = pd.to_numeric(df.Open)
        df.High = pd.to_numeric(df.High)
        df.Low = pd.to_numeric(df.Low)
        df.Close = pd.to_numeric(df.Close)
        df.Volume = pd.to_numeric(df.Volume)
        df = df.set_index('Date')
        # log.debug("df = " + str(df))
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        #     log.debug(df)
        # log.debug("df.info() = " + str(df.info()))
    return df, next_link_lc, previous_link_lc


def generate_dummy_df():
    global link_to_lm_until_datetime, link_to_lm_from_datetime
    column_names = ["Date", "Open", "High", "Low", "Close", "Volume"]
    df = pd.DataFrame(columns=column_names)
    df.Date = pd.to_datetime(df.Date)
    date_x = link_to_lm_from_datetime
    date_x_end = link_to_lm_until_datetime
    while date_x < date_x_end + timedelta(days=1):
        df = df.append({'Date': date_x, 'Open': 0, 'High': 0, 'Low': 0, 'Close': 0, 'Volume': 0}, ignore_index=True)
        date_x = date_x + timedelta(days=1)
    df = df.set_index('Date')
    return df


def reset_all_cnt():
    global button_live_cnt, button_day_cnt, button_week_cnt, button_month_cnt, button_4_months_cnt, button_year_cnt, \
        button_5_years_cnt, button_all_cnt
    button_live_cnt = 0
    button_day_cnt = 0
    button_week_cnt = 0
    button_month_cnt = 0
    button_4_months_cnt = 0
    button_year_cnt = 0
    button_5_years_cnt = 0
    button_all_cnt = 0
    return


def set_radio_button_state(button_live, button_day, button_week, button_month, button_4_months,
                           button_year, button_5_years, button_all):
    global button_live_cnt, button_day_cnt, button_week_cnt, button_month_cnt, button_4_months_cnt, button_year_cnt, \
        button_5_years_cnt, button_all_cnt
    global NEARLY_7_DAYS, NEARLY_31_DAYS
    global radio_button_state

    if button_live != button_live_cnt:
        if button_live > button_live_cnt:
            radio_button_state = radio_buttons.index('Live')
            button_live_cnt = button_live
        else:
            reset_all_cnt()
    elif button_day != button_day_cnt:
        if button_day > button_day_cnt:
            radio_button_state = radio_buttons.index('1 Day')
            button_day_cnt = button_day
        else:
            reset_all_cnt()
    elif button_week != button_week_cnt:
        if button_week > button_week_cnt:
            radio_button_state = radio_buttons.index('1 Week')
            button_week_cnt = button_week
        else:
            reset_all_cnt()
    elif button_month != button_month_cnt:
        if button_month > button_month_cnt:
            radio_button_state = radio_buttons.index('1 Month')
            button_month_cnt = button_month
        else:
            reset_all_cnt()
    elif button_4_months != button_4_months_cnt:
        if button_4_months > button_4_months_cnt:
            radio_button_state = radio_buttons.index('4 Months')
            button_4_months_cnt = button_4_months
        else:
            reset_all_cnt()
    elif button_year != button_year_cnt:
        if button_year > button_year_cnt:
            radio_button_state = radio_buttons.index('1 Year')
            button_year_cnt = button_year
        else:
            reset_all_cnt()
    elif button_5_years != button_5_years_cnt:
        if button_5_years > button_5_years_cnt:
            radio_button_state = radio_buttons.index('5 Years')
            button_5_years_cnt = button_5_years
        else:
            reset_all_cnt()
    elif button_all != button_all_cnt:
        if button_all > button_all_cnt:
            radio_button_state = radio_buttons.index('All Time')
            button_all_cnt = button_all
        else:
            reset_all_cnt()
    return


def set_time_frame_all():
    global NEARLY_7_DAYS, NEARLY_31_DAYS
    global radio_button_state, time_step_state, time_step_selection

    if radio_button_state == radio_buttons.index('Live'):
        time_frame_all_lc = timedelta(minutes=3*60)
        time_frame_lc = timedelta(minutes=3*60)
    elif radio_button_state == radio_buttons.index('1 Day'):
        time_frame_all_lc = timedelta(days=1)
        time_frame_lc = timedelta(days=1)
    elif radio_button_state == radio_buttons.index('1 Week'):
        time_frame_all_lc = NEARLY_7_DAYS
        time_frame_lc = NEARLY_7_DAYS
    elif radio_button_state == radio_buttons.index('1 Month'):
        time_frame_all_lc = NEARLY_31_DAYS
        if time_step_state == time_step_selection.index("Minute"):
            time_frame_lc = NEARLY_7_DAYS
        else:
            time_frame_lc = NEARLY_31_DAYS
    elif radio_button_state == radio_buttons.index('4 Months'):
        time_frame_all_lc = timedelta(days=122)
        if time_step_state == time_step_selection.index("Minute"):
            time_frame_lc = NEARLY_7_DAYS
        else:
            time_frame_lc = NEARLY_31_DAYS
    elif radio_button_state == radio_buttons.index('1 Year'):
        time_frame_all_lc = timedelta(days=366)
        if time_step_state == time_step_selection.index("Minute"):
            time_frame_lc = NEARLY_7_DAYS
        else:
            time_frame_lc = NEARLY_31_DAYS
    elif radio_button_state == radio_buttons.index('5 Years'):
        time_frame_all_lc = timedelta(days=4 * 365 + 367)
        if time_step_state == time_step_selection.index("Minute"):
            time_frame_lc = NEARLY_7_DAYS
        else:
            time_frame_lc = NEARLY_31_DAYS
    elif radio_button_state == radio_buttons.index('All Time'):
        time_frame_all_lc = timedelta(days=35 * 366)
        if time_step_state == time_step_selection.index("Minute"):
            time_frame_lc = NEARLY_7_DAYS
        else:
            time_frame_lc = NEARLY_31_DAYS
    else:
        time_frame_all_lc = None
        time_frame_lc = None

    return time_frame_all_lc, time_frame_lc

# Open a new browser tab:Dash is running on http://127.0.0.1:8050/


# ------------------------------------------------------------------------------
# App layout

def serve_layout():
    global radio_button_state
    log.debug("serve_layout()")
    layout_part_1 = [
        html.H1("Stock Charts", style={'textAlign': 'center'}),
        html.H2("(For demonstration purpose with a single user sessions only !)", style={'textAlign': 'center'}),
        html.H6("Change the value in the text box to set the ISIN"),
        html.Div(["ISIN: ",
                  dcc.Input(id='isin-input', value='', type='text')]),
        html.Div(id='instrument_output_name_id',
                 style={'textAlign': 'center', 'fontSize': '45px', 'fontWeight': 'bold',
                        'whiteSpace': 'pre'}),
        html.Div(id='instrument_output_values_id', style={'textAlign': 'center', 'fontSize': '21px',
                                                          'whiteSpace': 'pre'}),
        html.Br(),

        dcc.Dropdown(id="select_time_step",
                     options=[
                         {"label": "Minute", "value": "Minute"},
                         {"label": "Hour", "value": "Hour"},
                         {"label": "Day", "value": "Day"}],
                     multi=False,
                     value=time_step_selection[time_step_state],
                     style={'width': "30%"}
                     ),

        html.Div(id='time_step_output', children=[]),
        html.Br(),
        html.Button('Previous', id='button_previous', style=off_button_style, n_clicks=0),
        html.Button('Next', id='button_next', style=off_button_style, n_clicks=0),
        html.Div(id='output_total_time_range_button',
                 children='Time'),
        html.Div(id='output_time_range_button',
                 children='Time'),
        html.Div(id='output_error_message',
                 children='No Error', style={'textAlign': 'left', 'color': 'red', 'backgroundColor': 'white'}),
        html.Br(),
        html.A(html.Button('Auto Refresh on/off'), href='/'),
        html.Button('Live', id='button_live', style={'fontSize': '21px', 'borderRadius': '15px',
                                                     'margin': '8px 10px', 'border': 'solid'}, n_clicks=0),
        html.Button('Day', id='button_day', style={'fontSize': '21px', 'borderRadius': '15px',
                                                   'margin': '8px 10px', 'border': 'solid'}, n_clicks=0),
        html.Button('Week', id='button_week', style={'fontSize': '21px', 'borderRadius': '15px',
                                                     'margin': '8px 10px', 'border': 'solid'}, n_clicks=0),  # * 7
        html.Button('Month', id='button_month', style={'fontSize': '16px', 'borderRadius': '15px',
                                                       'margin': '8px 10px', 'border': 'solid'}, n_clicks=0),  # * 4
        html.Button('4 Month', id='button_4_month', style={'fontSize': '16px', 'borderRadius': '15px',
                                                           'margin': '8px 10px', 'border': 'solid'}, n_clicks=0),
        # * 4
        html.Button('year', id='button_year', style={'fontSize': '16px', 'borderRadius': '15px',
                                                     'margin': '8px 10px', 'border': 'solid'}, n_clicks=0),  # * 3
        html.Button('5 Year', id='button_5_year', style={'fontSize': '16px', 'borderRadius': '15px',
                                                         'margin': '8px 10px', 'border': 'solid'}, n_clicks=0),
        # * 5
        html.Button('All', id='button_all', style={'fontSize': '16px', 'borderRadius': '15px',
                                                   'margin': '8px 10px', 'border': 'solid'}, n_clicks=0),
        html.Br(),
        dcc.Graph(id='my_stock_chart_2', figure={}),
        dcc.Graph(id='my_stock_chart_1', figure={})]
    if radio_button_state == 0:  # = Live
        layout_part_1.append(
            dcc.Interval(
                id='interval-component',
                interval=TIMER_INTERVAL,  # in milliseconds
                n_intervals=0
            ))
    else:
        layout_part_1.append(
            dcc.Interval(
                id='interval-component',
                interval=TIMER_INTERVAL_LONG,  # in milliseconds
                n_intervals=0
            ))
    my_layout = html.Div(layout_part_1, style={'backgroundColor': colors['background']})
    return my_layout


app.layout = serve_layout


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='instrument_output_name_id', component_property='children'),
     Output(component_id='instrument_output_values_id', component_property='children'),
     Output(component_id='time_step_output', component_property='children'),
     Output(component_id='my_stock_chart_1', component_property='figure'),
     Output(component_id='my_stock_chart_2', component_property='figure'),
     Output(component_id='output_total_time_range_button', component_property='children'),
     Output(component_id='output_time_range_button', component_property='children'),
     Output(component_id='output_error_message', component_property='children'),
     Output(component_id='button_live', component_property='style'),
     Output(component_id='button_day', component_property='style'),
     Output(component_id='button_week', component_property='style'),
     Output(component_id='button_month', component_property='style'),
     Output(component_id='button_4_month', component_property='style'),
     Output(component_id='button_year', component_property='style'),
     Output(component_id='button_5_year', component_property='style'),
     Output(component_id='button_all', component_property='style')],
    [Input(component_id='isin-input', component_property='value'),
     Input(component_id='button_previous', component_property='n_clicks'),
     Input(component_id='button_next', component_property='n_clicks'),
     Input(component_id='button_live', component_property='n_clicks'),
     Input(component_id='button_day', component_property='n_clicks'),
     Input(component_id='button_week', component_property='n_clicks'),
     Input(component_id='button_month', component_property='n_clicks'),
     Input(component_id='button_4_month', component_property='n_clicks'),
     Input(component_id='button_year', component_property='n_clicks'),
     Input(component_id='button_5_year', component_property='n_clicks'),
     Input(component_id='button_all', component_property='n_clicks'),
     Input(component_id='select_time_step', component_property='value'),
     Input(component_id='interval-component', component_property='n_intervals')]
)
def update_graph(isin_input_value, button_previous, button_next, button_live, button_day, button_week, button_month,
                 button_4_month,
                 button_year, button_5_year, button_all, option_selected, n_timer):
    global link_to_lm, link_to_lm_until_datetime, link_to_lm_from_datetime, time_frame_all, time_frame
    global button_previous_cnt, button_next_cnt
    global previous_link, next_link
    global button_color_live, button_color_day, button_color_week, button_color_month, button_color_4_months, \
        button_color_year, button_color_5_years, button_color_all
    global time_step_state, n_timer_cnt, isin

    # serve_layout()
    df = pd.DataFrame()

    if n_timer != n_timer_cnt:
        n_timer_cnt = n_timer
        log.info("n_timer = " + str(n_timer))

    if isin_input_value != "":
        isin = isin_input_value.strip()
    if isin != "":
        log.info("isin = [" + isin + "]")
        time_step_output = ""

        start_time_begin = datetime.datetime.today()  # just define type of variable
        end_time = datetime.datetime.today()  # just define type of variable

        # log.debug("button_previous, button_next, button_live, button_day, button_week, button_month, button_4_month, " +
        #           "button_year, button_5_year, button_all = " + str(button_previous) + str(button_next) +
        #           str(button_live) + str(button_day) + str(button_week) + str(button_month) +
        #           str(button_4_month) + str(button_year) + str(button_5_year) + str(button_all))

        if option_selected == "Minute":
            time_step_state = time_step_selection.index("Minute")
        elif option_selected == "Hour":
            time_step_state = time_step_selection.index("Hour")
        elif option_selected == "Day":
            time_step_state = time_step_selection.index("Day")

        log.info("Time_Step = " + time_step_selection[time_step_state])

        if time_step_state == time_step_selection.index("Minute"):
            time_step = "m1"
        elif time_step_state == time_step_selection.index("Hour"):
            time_step = "h1"
        elif time_step_state == time_step_selection.index("Day"):
            time_step = "d1"
        else:
            time_step = None

        if button_previous != button_previous_cnt:
            if button_previous > button_previous_cnt:
                button_previous_cnt = button_previous
                link_to_lm = previous_link
                df, next_link, previous_link = retrieve_data(link_to_lm)
            else:
                button_previous_cnt = 0
        elif button_next != button_next_cnt:
            if button_next > button_next_cnt:
                button_next_cnt = button_next
                link_to_lm = next_link
                df, next_link, previous_link = retrieve_data(link_to_lm)
            else:
                button_next_cnt = 0
        else:
            set_radio_button_state(button_live, button_day, button_week, button_month,
                                   button_4_month, button_year, button_5_year, button_all)
            time_frame_all, time_frame = set_time_frame_all()

            log.info("time_frame = " + str(time_frame))
            log.info("time_frame_all = " + str(time_frame_all))
            time_step_output = "The time step chosen by user was: {}, ".format(option_selected) + \
                               " for  " + radio_buttons[radio_button_state] + " with sub-time range " + str(time_frame)
            log.info("option_selected = " + str(option_selected))

            datetime_today = datetime.datetime.today()
            start_time = datetime_today - time_frame_all

            # Do no request old data which arw not available
            if start_time < datetime.datetime(2021, 4, 1, 0, 0):
                start_time = datetime.datetime(2021, 4, 1, 0, 0)

            start_time_str = str((time.mktime(start_time.timetuple())))
            start_time_begin = start_time

            datetime_x = start_time
            end_time = datetime_x + time_frame

            # Do no request  data from the future
            if end_time > datetime_today:
                end_time = datetime_today

            end_time_str = str((time.mktime(end_time.timetuple())))
            link_to_lm = f"https://paper.lemon.markets/rest/v1/trading-venues/{mic}/instruments/{isin}/data/ohlc/{time_step}/?date_until={end_time_str}&date_from={start_time_str}"
            log.debug("first link_to_lm =" + link_to_lm)
            df, next_link, previous_link = retrieve_data(link_to_lm)
            log.debug(str(datetime_x) + " ### " + str(datetime_today))
            while (datetime_x + time_frame) < datetime_today:
                log.debug(str(datetime_x) + " ### " + str(datetime_today))
                datetime_x = datetime_x + time_frame
                start_time = datetime_x
                start_time_str = str((time.mktime(start_time.timetuple())))
                end_time = start_time + time_frame
                # Do no request  data from the future
                if end_time > datetime_today:
                    end_time = datetime_today
                end_time_str = str((time.mktime(end_time.timetuple())))
                log.debug(str(start_time) + " === " + str(end_time))
                link_to_lm = f"https://paper.lemon.markets/rest/v1/trading-venues/{mic}/instruments/{isin}/data/ohlc/{time_step}/?date_until={end_time_str}&date_from={start_time_str}"
                log.debug("second link_to_lm =" + link_to_lm)
                ddf, next_link, previous_link = retrieve_data(link_to_lm)
                df = df.append(ddf)

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        #     log.info(df)
        # Calculate until and from-time from url-link
        #  https://paper.lemon.markets/rest/v1/trading-venues/XMUN/instruments/US67066G1040/data/ohlc/h1/?date_until=1622464762.0&date_from=1619786362.672001
        link_to_lm_until_from = link_to_lm.split("=", 2)
        link_to_lm_until = link_to_lm_until_from[1].split("&", 1)
        link_to_lm_until_datetime = datetime.datetime.fromtimestamp(float(link_to_lm_until[0]))
        link_to_lm_from_str = link_to_lm.split("=", 2)
        link_to_lm_from_datetime = datetime.datetime.fromtimestamp(float(link_to_lm_from_str[2]))

        sub_time_range_str = "The last used sub-time range: " + link_to_lm_from_datetime.strftime(
            "%d-%b-%Y (%H:%M:%S) - ") + link_to_lm_until_datetime.strftime("%d-%b-%Y (%H:%M:%S)")

        time_range_str = "The last used total-time range:  " + start_time_begin.strftime(
            "%d-%b-%Y (%H:%M:%S) - ") + end_time.strftime("%d-%b-%Y (%H:%M:%S)")
        if df.empty:
            df = generate_dummy_df()
            error_message = "No data available for this time frame"
        else:
            error_message = None
        # Plotly Express
        figure_line = px.line(df, x=df.index, y=["Open", "Close", "Low", "High"])

        # Plotly Graph Objects
        figure_candlesticks = go.Figure(
            data=[
                go.Candlestick(
                    x=df.index,
                    low=df["Low"],
                    high=df["High"],
                    open=df["Open"],
                    close=df["Close"]
                )
            ]
        )
        # Retrieve a single Trading Venue instrument
        link_to_lm_instrument = f"https://paper.lemon.markets/rest/v1/trading-venues/{mic}/instruments/{isin}/"
        request = requests.get(link_to_lm_instrument, headers={"Authorization": authorization})
        # log.info(request)
        if str(request) == "<Response [200]>":
            # log.info(request)
            instrument = json.loads(request.content)
            # log.info(json.dumps(instrument, indent=4, sort_keys=True))

            instrument_output_name = instrument['title']
            instrument_output_values = "ISIN: " + isin + "   " + \
                                       "   WKN: " + instrument['wkn'] + "   Symbol: " + instrument['symbol'] + "   Type: " + \
                                       instrument[
                                           'type']
        else:
            instrument_output_name = ""
            instrument_output_values = ""
    else:
        instrument_output_name = ""
        instrument_output_values = ""
        time_step_output = ""
        time_range_str = ""
        sub_time_range_str = ""
        df = generate_dummy_df()
        error_message = "No data available"
        figure_line = px.line(df, x=df.index, y=["Open", "Close", "Low", "High"])
        figure_candlesticks = go.Figure(
            data=[
                go.Candlestick(
                    x=df.index,
                    low=df["Low"],
                    high=df["High"],
                    open=df["Open"],
                    close=df["Close"]
                )
            ]
        )

    button_color_live = off_button_style
    button_color_day = off_button_style
    button_color_week = off_button_style
    button_color_month = off_button_style
    button_color_4_months = off_button_style
    button_color_year = off_button_style
    button_color_5_years = off_button_style
    button_color_all = off_button_style

    log.info("radio_button_state = " + radio_buttons[radio_button_state])
    if radio_button_state == radio_buttons.index("Live"):
        button_color_live = on_button_style
    elif radio_button_state == radio_buttons.index("1 Day"):
        button_color_day = on_button_style
    elif radio_button_state == radio_buttons.index("1 Week"):
        button_color_week = on_button_style
    elif radio_button_state == radio_buttons.index("1 Month"):
        button_color_month = on_button_style
    elif radio_button_state == radio_buttons.index("4 Months"):
        button_color_4_months = on_button_style
    elif radio_button_state == radio_buttons.index("1 Year"):
        button_color_year = on_button_style
    elif radio_button_state == radio_buttons.index("5 Years"):
        button_color_5_years = on_button_style
    elif radio_button_state == radio_buttons.index("All Time"):
        button_color_all = on_button_style

    return '{}'.format(instrument_output_name), '{}'.format(instrument_output_values), \
           time_step_output, figure_line, figure_candlesticks, time_range_str, sub_time_range_str, \
           error_message, button_color_live, button_color_day, button_color_week, button_color_month, button_color_4_months, \
           button_color_year, button_color_5_years, button_color_all


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    log.info("here is __main__")
    app.run_server(debug=True)

# Dash is running on http://127.0.0.1:8050/
#
# * Serving Flask app 'plot_candlestick_w_dash - PRIVAT' (lazy loading)
# * Environment: production
#   WARNING: This is a development server. Do not use it in a production deployment.
#   Use a production WSGI server instead.
# * Debug mode: on
