import casparser
import pandas as pd
import json
from pyxirr import xirr


def getLatest(URL_ALL='https://www.amfiindia.com/spages/NAVAll.txt'):
    dt = pd.read_csv(URL_ALL)
    dt = dt.rename(columns={
                   'Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date': 1})
    t = dt[1].str.split(';', expand=True)
    t.columns = ['amfi', 'ISIN Div Payout/ ISIN Growth',
                 'ISIN Div Reinvestment', 'Scheme Name', 'nav', 'Date']
    t = t.dropna(how='any')
    t['Date'] = pd.to_datetime(t['Date'])
    return t


def getXirr(df, df_All):
    amfi_code = str(df.amfi.iloc[0])
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
    data = casparser.read_cas_pdf(filename, password, output="json")
    d = json.loads(data)
    name = d['investor_info']['name']
    statementPeriod = d['statement_period']
    return name.title(), statementPeriod


def getData(filename, password):
    data = casparser.read_cas_pdf(filename, password, output="csv")
    f = open("temp.csv", "w")
    f.write(data)
    f.close()
    df = pd.read_csv('temp.csv', index_col=['date'])
    amcs = df.amc.unique()
    print(amcs)
    schemes = df.scheme.unique()
    print(schemes)

    df2 = df[['type', 'amount', 'units', 'nav', 'balance', 'scheme', 'amfi']].loc[(
        df.type == 'PURCHASE') | (df.type == 'REDEMPTION')]
    df_All = getLatest()

    userData = []
    for scheme in schemes:
        df = df2.loc[df2.scheme == scheme]
        df['investment'] = df.amount.cumsum()
        inv = round(df['investment'].iloc[-1], 2)
        bal = round(df['balance'].iloc[-1], 2)
        nav = round(df['nav'].iloc[-1], 2)
        curr = round(bal*nav, 2)
        ret = round(((curr-inv)*(100/inv)), 2)
        if bal == 0:
            continue
        if len(df) == 1:
            xirr_amount = 0
        else:
            xirr_amount = round(getXirr(df=df, df_All=df_All)*100, 2)
        user = {'scheme': scheme, 'balance': bal,
                'investment': inv, 'nav': nav,
                'current': curr, 'return': ret,
                'xirr': xirr_amount}
        userData.append(user)

    name, statementPeriod = getNameAndPeriod(filename, password)

    return userData, name, statementPeriod
