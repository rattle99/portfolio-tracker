import casparser
import pandas as pd
import json
from pyxirr import xirr


def getXirr(df):
    df = df.assign(val=df['nav']*df['balance'])
    b1 = df.iloc[-2].loc['balance']
    b2 = df.iloc[-1].loc['nav']
    b3 = b1*b2
    amt = df['amount'].copy()
    amt[-1] = -1*b3
    amt.index = pd.to_datetime(amt.index)
    return xirr(amt)


def getName(filename, password):
    data = casparser.read_cas_pdf(filename, password, output="json")
    d = json.loads(data)
    name = d['investor_info']['name']
    return name.title()


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

    userData = []
    for scheme in schemes:
        df = df2[['type', 'amount', 'units', 'nav',
                  'balance', 'scheme']].loc[df2.scheme == scheme]
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
            xirr_amount = round(getXirr(df)*100, 2)
        user = {'scheme': scheme, 'balance': bal,
                'investment': inv, 'nav': nav,
                'current': curr, 'return': ret,
                'xirr': xirr_amount}
        userData.append(user)

    name = getName(filename, password)

    return userData, name
