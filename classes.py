import json
import requests
import datetime
import csv
import sqlite3



file_name_dblogs = "logs.db"
file_name_csvstats = "todaystats.csv"
file_name_dbstats = "stats.db"


class Logs:
    def __init__(self) -> None:
        conn = sqlite3.connect(file_name_dblogs)
        with conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS logs(
            log_id INTEGER primary key,
            user TEXT,
            function TEXT,
            message TEXT,
            time INTEGER
            );''')

    def addLog(self, new_log: dict) -> None:
        conn = sqlite3.connect(file_name_dblogs)
        with conn:
            c = conn.cursor()
            c.execute('''INSERT into logs(user, function, message, time) VALUES(?,?,?,?)''', list(new_log.values()))

    def addLogs(self, new_logs: list) -> None:
        conn = sqlite3.connect(file_name_dblogs)
        with conn:
            c = conn.cursor()
            for new_log in new_logs:
                c.execute('''INSERT into logs(user, function, message, time) VALUES(?,?,?,?)''', list(new_log.values()))

    def getLastFiveLogs(self) -> list:
        ans = []
        conn = sqlite3.connect(file_name_dblogs)
        with conn:
            c = conn.cursor()
            c.execute('''SELECT user, function, message, time from logs''')
            data = c.fetchall()
            # print(data)
            if len(data) > 5:
                data = data[-1:-6:-1]
            for row in data:
                ans.append(
                    {"user": row[0], "function": row[1], "message": row[2], "time": row[3]}
                )
        # print(ans)
        return ans[::-1]


class CSVStats:
    date = datetime.date.today().strftime("%m-%d-%Y")
    def __init__(self, file_name) -> None:
        self.filename = file_name
        self.topfive = []
        self.fulldata = []
        # f = open( file_name_dbstats, 'w' )
        # f.close()
        self.conn = sqlite3.connect(file_name_dbstats)
        with self.conn:
            c = self.conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS topfive(
            date TEXT,
            province TEXT,
            new_infected INTEGER);''')
            c.execute(
                '''SELECT province, new_infected FROM topfive WHERE date = ? ORDER BY new_infected DESC;''',
                [self.date]
            )
            self.fulldata = []
            ans = c.fetchall()
            if len(ans) != 0:
                for row in ans:
                    self.fulldata.append({"province" : row[0], "new infected" : row[1]})
                    self.status_code = 200
                keys = list(self.fulldata[0].keys())
                with open(self.filename, 'w') as output_file:
                    dict_writer = csv.DictWriter(output_file, fieldnames=keys)
                    dict_writer.writeheader()
                    dict_writer.writerows(self.fulldata)
            else:
                self.r = requests.get(
                    f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{self.date}.csv')  # noqa
                self.status_code = self.r.status_code
                with open(self.filename, "wb") as f:
                    f.write(self.r.content)


    def changeRequest(self) -> None:
        self.r = requests.get(
            f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{self.date}.csv')# noqa
        self.status_code = self.r.status_code
        if self.status_code == 200:
            with open(self.filename, "wb") as f:
                f.write(self.r.content)

    def getTopFiveProvinces(self) -> list:
        if len(self.topfive) == 0:
            with open(self.filename, "r") as f:
                stats = csv.DictReader(f)
                top_five = []
                for row in stats:
                    place = row["Province_State"] + " " + row["Country_Region"] \
                        if row["Province_State"] != "" else row["Country_Region"]
                    new_infected = int(row["Confirmed"]) - int(row["Deaths"]) - int(row["Recovered"])
                    if len(top_five) == 0:
                        top_five.append({"province": place, "new infected": new_infected})
                    else:
                        for i in range(len(top_five)):
                            if top_five[i]["new infected"] <= new_infected:
                                top_five.insert(i, {"province": place, "new infected": new_infected})
                                break
                if len(top_five) < 5:
                    self.topfive = top_five
                with self.conn:
                    c = self.conn.cursor()
                    c.execute('''CREATE TABLE IF NOT EXISTS topfive(
                        date TEXT,
                        province TEXT,
                        new_infected INTEGER);''')
                    for elem in top_five:
                        a = [self.date]
                        a += list(elem.values())
                        # print(a)
                        c.execute('''INSERT INTO topfive(date, province, new_infected) VALUES(?,?,?)''', a)
                    self.topfive = top_five[0:5]
        return self.topfive
