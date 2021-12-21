import casparser
import pandas as pd
import json
from pyxirr import xirr


def getLatest(URL_ALL='https://www.amfiindia.com/spages/NAVAll.txt'):
    """Returns a dataframe with the latest NAV of all mutual funds of the current day.

    Args:
        URL_ALL (str, optional): URL to fetch data from. Defaults to 'https://www.amfiindia.com/spages/NAVAll.txt'.

    Returns:
        obj: A pandas dataframe.
    """

    dt = pd.read_csv(URL_ALL)
    dt = dt.rename(columns={
                   'Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date': 1})
    t = dt[1].str.split(';', expand=True)
    t.columns = ['amfi', 'ISIN Div Payout/ ISIN Growth',
                 'ISIN Div Reinvestment', 'Scheme Name', 'nav', 'Date']
    t = t.dropna(how='any')
    t['Date'] = pd.to_datetime(t['Date'])
    return t


def getFundXirr(df, df_All):
    """Calculate XIRR for investments made into a particular fund.

    Args:
        df (obj): Pandas dataframe of transactions for a particular fund.
        df_All (obj): Pandas dataframe of latest NAVs of all funds for the day.

    Returns:
        float: Calculated XIRR value.
    """

    amfi_code = str(int(df.amfi.iloc[0]))
    df_fund = df_All.loc[df_All['amfi'] == amfi_code]
    b1 = df.iloc[-1].loc['balance'].copy()
    b2 = float(df_fund.nav)
    b3 = -1*(b1*b2)
    df_xirr = df.amount.copy()
    df_xirr = df_xirr.reset_index()
    df_xirr = df_xirr.append({'date': pd.to_datetime(
        df_fund.Date.iloc[0]), 'amount': b3}, ignore_index=True)
    return xirr(df_xirr)


def getNameAndPeriod(filename, password):
    """Fetch name of user and the statement time period from CAS file.

    Args:
        filename (str): File path for CAS file to read from.
        password (str): Password to open CAS file.

    Returns:
        str: Name of user.
        dict: Dictionary with from and to date for account statement period.
    """

    data = casparser.read_cas_pdf(filename, password, output="json")
    d = json.loads(data)
    name = d['investor_info']['name']
    statementPeriod = d['statement_period']
    return name.title(), statementPeriod


def getData(filename, password, df_tx):
    """Fetches and calculate fund data for user in terms of investments, returns generated, XIRR, etc. 
    Uses helper functions inside.

    Args:
        filename (str): File path for CAS file to read from.
        password (str): Password to open CAS file.
        df_tx (obj): Dataframe of user transactions.

    Returns:
        list: A list of dictionaries with data for each individual fund for each element in list.
        str: Name of user.
        dict: Dictionary with from and to date for account statement period.
    """

    df2 = df_tx
    df_All = getLatest()

    schemes = df2.scheme.unique()
    print("Schemes tracked: ", len(schemes))
    print(schemes)
    print()

    userData = []
    for scheme in schemes:
        df = df2.loc[df2.scheme == scheme]
        df['investment'] = df.amount.cumsum()
        amfi_code = str(int(df.amfi.iloc[0]))
        df_fund = df_All.loc[df_All['amfi'] == amfi_code]

        inv = round(df['investment'].iloc[-1], 2)
        bal = round(df['balance'].iloc[-1], 2)
        try:
            nav = round(float(df_fund['nav'].iloc[-1]), 2)
        except IndexError:
            print(df_fund)
            print()
            print(df_fund['nav'])
            print()
            print(scheme)
            print()

        curr = round(bal*nav, 2)
        ret = round(((curr-inv)*(100/inv)), 2)

        if bal == 0:
            continue
        else:
            xirr_amount = round(getFundXirr(df=df, df_All=df_All)*100, 2)
        fund = {'scheme': scheme, 'balance': bal,
                'investment': inv, 'nav': nav,
                'current': curr, 'return': ret,
                'xirr': xirr_amount}
        userData.append(fund)

    name, statementPeriod = getNameAndPeriod(filename, password)

    return userData, name, statementPeriod


def getTransactions(filename, password):
    data = casparser.read_cas_pdf(filename, password, output="csv")
    f = open("temp.csv", "w")
    f.write(data)
    f.close()
    df = pd.read_csv('temp.csv', index_col=['date'])
    COLUMNS_WANTED = ['type', 'amount', 'units',
                      'nav', 'balance', 'scheme', 'amfi']
    df = df[COLUMNS_WANTED].loc[(
        df.type == 'PURCHASE') | (df.type == 'REDEMPTION') | (df.type == 'DIVIDEND_REINVEST') | (df.type == 'PURCHASE_SIP')]
    df = df.dropna()
    df = df.sort_index()

    return df


def finalParser(filename, password):
    """Fetches and calculate fund data for user in terms of investments, returns generated, XIRR, etc. 
    Account summary, user name and statement period. Uses helper functions inside.

    Args:
        filename (str): File path for CAS file to read from.
        password (str): Password to open CAS file.

    Returns:
        list: A list of dictionaries with data for each individual fund for each element in list.
        str: Name of user.
        dict: Dictionary with from and to date for account statement period.
        dict: Dictionary for total portfolio summary with metrics for investment amount, current 
        amount, PnL, XIRR, etc.
    """

    df = getTransactions(filename=filename, password=password)

    userData, name, statementPeriod = getData(filename, password, df_tx=df)
    investment = 0
    current = 0
    for fund in userData:
        investment += fund['investment']
        current += fund['current']

    df_xirr = df.amount.copy()
    df_xirr = df_xirr.reset_index()
    today = pd.to_datetime("today")
    amt = -1*current
    df_xirr = df_xirr.append(
        {'date': today, 'amount': amt}, ignore_index=True)
    xirr_amount = round(xirr(df_xirr)*100, 2)
    print(xirr_amount)
    pnl = round(current - investment, 2)
    if investment == 0:
        ret = 0
    else:
        ret = round(((current-investment)*(100/investment)), 2)
    current = round(current, 2)
    investment = round(investment, 2)
    summary = {'investment': investment, 'current': current,
               'pnl': pnl, 'return': ret, 'xirr': xirr_amount}

    return userData, name, statementPeriod, summary
