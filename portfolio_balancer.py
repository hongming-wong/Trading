import sqlite3
from sqlite3 import Error
import requests
import os


def get_quote(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv('API_KEY')}"
    r = requests.get(url)
    data = r.json()
    return float(data.get('Global Quote').get('05. price'))


def create_table():
    conn = None
    try:
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()

        sql_command = """
            CREATE TABLE IF NOT EXISTS portfolio(
            date TEXT PRIMARY KEY,
            us_equity DOUBLE,
            int_equity DOUBLE,
            bonds DOUBLE);
            """

        cursor.execute(sql_command)
    except Error as e:
        print("Something went wrong creating table")
        print(e)
    if conn:
        conn.close()


def insert(us_equity, int_equity, bonds):
    conn = None
    try:
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()

        sql_command = f"""
            INSERT INTO portfolio(date, us_equity, int_equity, bonds)
            VALUES (datetime('now'), {us_equity}, {int_equity}, {bonds});
        """

        cursor.execute(sql_command)
        conn.commit()
    except Error as e:
        print("Something went wrong during insertion")
        print(e)
    if conn:
        conn.close()


def select():
    conn = None
    try:
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()

        sql_command = f"""
            SELECT * FROM portfolio
            ORDER BY date 
            DESC LIMIT 1;
        """

        cursor.execute(sql_command)
        rows = cursor.fetchall()
        conn.close()
        return rows

    except Error as e:
        print("Something went wrong during selection")
        print(e)
    if conn:
        conn.close()


class Security:
    def __init__(self, name, qty):
        self.name = name
        self.qty = qty
        self.price = None

    def get_value(self):
        self.price = get_quote(self.name)
        return self.qty * self.price

    def update_qty(self, qty):
        self.qty = self.qty + qty


class Portfolio:
    def __init__(self):
        self.cash = 0

        self.portfolio = {
            'us_equity': [Security('VTI', 4), Security('AAPL', 1)],
            'int_equity': [Security('VWO', 5)],
            'bonds': [Security('BND', 3)]
        }

        self.target_allocation = {
            'us_equity': 0.65,
            'int_equity': 0.20,
            'bonds': 0.15
        }


    def total_value(self):
        total = 0
        for key in self.portfolio:
            for security in self.portfolio[key]:
                total += security.get_value()

        return total

    def structure(self):
        for key in self.portfolio:
            for item in self.portfolio[key]:
                print(item.name, item.qty)

    def describe(self):
        total = 0
        lst = []
        for key in self.portfolio:
            subtotal = 0
            for security in self.portfolio[key]:
                subtotal += security.get_value()
            lst.append((key, subtotal))
            total += subtotal

        for key, value in lst:
            print(f"***{key}***")
            print(f"value: {value}")
            print(f"proportion: {value / total}")

        print(f"total: {total}")

    def balance(self):
        us_equity = sum(p.get_value() for p in self.portfolio['us_equity'])
        int_equity = sum(p.get_value() for p in self.portfolio['int_equity'])
        bonds = sum(p.get_value() for p in self.portfolio['bonds'])
        insert(us_equity=us_equity,
               int_equity=int_equity,
               bonds=bonds)
        total = us_equity + int_equity + bonds
        us = (us_equity / total - self.target_allocation['us_equity']) * total
        it = (int_equity / total - self.target_allocation['int_equity']) * total
        bd = (bonds / total - self.target_allocation['bonds']) * total

        # sell first
        if us > 0:
            self.order(self.portfolio['us_equity'][0], us)
        if it > 0:
            self.order(self.portfolio['int_equity'][0], it)
        if bd > 0:
            self.order(self.portfolio['bonds'][0], bd)

        # then buy
        if us < 0:
            self.order(self.portfolio['us_equity'][0], us)
        if it < 0:
            self.order(self.portfolio['int_equity'][0], it)
        if bd < 0:
            self.order(self.portfolio['bonds'][0], bd)


    def order(self, security: Security, amount):
        qty = amount/security.price
        # insert logic here
        self.portfolio[security.name][0].update_qty(qty)



if __name__ == "__main__":
    dummy = Portfolio()
    dummy.balance()
    dummy.structure()
