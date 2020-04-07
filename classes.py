import json
import requests
import datetime
import csv


class Logs:
    def __init__(self, file_name):
        self.file_name = file_name
        f = open(file_name, "r")
        f.close()

    def addLog(self, new_log):
        with open(self.file_name, "a") as write_file:
            write_file.write(json.dumps(new_log) + "\n")

    def addLogs(self, newlogs):
        with open(self.file_name, "a") as write_file:
            for new_log in newlogs:
                write_file.write(json.dumps(new_log) + "\n")

    def getLastFiveLogs(self):
        ans = []
        with open(self.file_name, "r") as read_file:
            data = read_file.readlines()
            if len(data) > 5:
                data = data[-1:-6:-1]
            for elems in data:
                log = json.loads(elems)
                ans.append(log)
            return ans


class CSVStats:
    date = datetime.date.today().strftime("%m-%d-%Y")
    def __init__(self, file_name):
        self.filename = file_name
        self.r = requests.get(
            f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{self.date}.csv')
        self.status_code = self.r.status_code
        if self.status_code == 200:
            with open(self.filename, "wb") as f:
                f.write(self.r.content)

    def changeRequest(self):
        self.r = requests.get(
            f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{self.date}.csv' )
        self.status_code = self.r.status_code
        if self.status_code == 200:
            with open(self.filename, "wb" ) as f:
                f.write(self.r.content )

    def getTopFiveProvinces(self):
        top_five = []
        with open(self.filename, "r") as f:
            stats = csv.DictReader(f)
            for row in stats:
                place = row["Province_State"] + " " + row["Country_Region"] if row["Province_State"]!= "" else row["Country_Region"]
                new_infected = int(row["Confirmed"]) - int(row["Deaths"]) - int(row["Recovered"])
                if len(top_five) == 0:
                    top_five.append({"province": place, "new infected": new_infected})
                else:
                    for i in range(len(top_five)):
                        if top_five[i]["new infected"] <= new_infected:
                            top_five.insert(i, {"province": place, "new infected": new_infected})
                            break
        return top_five
