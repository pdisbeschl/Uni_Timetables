"""
This class is supposed to process constraints and to transform them into
an uniform way which all the algorithms can read
author: Huy Ngo
author: Yu Fee Chan
author: Daniel Kaestner
author: Paul Disbeschl
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim

We are currently working with timestamp

Documented following PEP 257.
"""

import pandas as pd
from datetime import datetime, timedelta
import os

class ConstraintParser():
    logFile = open(os.path.realpath('./Logs/log.txt'), "a")

    def __init__(self):
        #Dictionaries with information about the period, holidays, courses, rooms and lecturers
        self.period_info = {}
        self.courses = {}
        self.rooms = {}
        self.lecturers = {}
        self.holidays = {}
        self.free_timeslots = {}
        self.read_excel()

    def read_excel(self):
        self.logFile.write('Reading hard constraints\n')
        #Load the excel file and transform them into dictionaries which we can use for the algorithms
        xls = pd.ExcelFile(os.path.realpath('./InputOutput/Sample.xlsx'))
        courses_df = pd.read_excel(xls, 'Courses')
        rooms_df = pd.read_excel(xls, 'Rooms')
        holidays_df = pd.read_excel(xls, 'Holidays')
        period_info_df = pd.read_excel(xls, 'PeriodInfo')
        lecturers_df = pd.read_excel(xls, 'Lecturers')

        #Create a dictionary with the shape {CourseID : {Programme: BAY1, ...}} and likewise for all the other files
        self.logFile.write('Reading courses\n')
        courses_df["Lecturers"] = courses_df["Lecturers"].apply(lambda x: x.replace(" ", ""))
        courses_df = courses_df.set_index("CourseID").transpose().to_dict()
        self.courses = courses_df
        self.logFile.write(str(self.courses) + '\n\n')

        self.logFile.write('Reading rooms\n')
        self.rooms = rooms_df.set_index("RoomID").transpose().to_dict()
        self.logFile.write(str(self.rooms) + '\n\n')

        self.logFile.write('Reading period info\n')
        self.period_info = period_info_df.apply(pd.to_datetime).to_dict('records')[0]
        self.logFile.write(str(self.period_info) + '\n\n')

        self.logFile.write('Reading holidays\n')
        self.holidays = self.load_holidays(holidays_df)
        self.logFile.write(str(self.holidays) + '\n\n')

        self.logFile.write('Reading Lecturers\n')
        self.lecturers = self.load_lecturers(lecturers_df)
        self.logFile.write(str(self.lecturers) + '\n\n')

        self.logFile.write('Generate a list of free timeslots\n')
        self.free_timeslots = self.generate_timeslots()
        self.logFile.write(str(self.free_timeslots) + '\n\n')

        self.logFile.write('Reading of hard constraints complete\n')

    def generate_timeslots(self): #The holidays are lists with binary integer variables (key - value pair), indicating if it's a holiday or not
        free_timeslots = []
        for date, holiday in self.holidays.items():
            if not holiday:
                for i in range(0,4):
                    hour = int(8 + 2*i + (((i + 1) * 30) / 60))
                    start = date.replace(hour=hour, minute=((30+i*30)%60))
                    free_timeslots.append(start)
        return free_timeslots

    """
    Generate a dictionary in the format (Timestamp : [0,1]), where 1 indicates that a day is a holiday and no lectures can happen
    It covers all dates for a given period and flags all weekend days as a holidays and additional holidays can be added
    in the excel file.
    @param holidays_df a dataframe with specified dates where no lectures should happen
    @return holidays a dict which covers all dates in a period and indicates if a lecture can happen
    """
    def load_holidays(self, holidays_df):
        holidays_df['Date'] = pd.to_datetime(holidays_df['Date'], format="%d.%m.%Y")
        holidays_df["Holiday"] = 1
        self.holidays = holidays_df.set_index('Date').to_dict()
        self.holidays = self.holidays["Holiday"]
        date_counter = self.period_info['StartDate']

        while date_counter <= self.period_info['EndDate']:
            if date_counter.weekday() < 5 and date_counter not in self.holidays:
                self.holidays[date_counter] = 0
            else:
                self.holidays[date_counter] = 1
            date_counter += timedelta(days=1)
        return self.holidays

    """
    Generate a dictionary for lectures which contains a all dates where a lecturer is not available
    @param lectures_df dataframe with all dates where a lecturer is not available
    @return lecturers a dict in form {lecturer: {date1:[from,to], date2:[from,to],...},...}
    """
    def load_lecturers(self, lecturers_df):
        #Group unavailabilities for each lecturer
        for lecturer in lecturers_df.groupby("Lecturer"):
            name = lecturer[0].replace(" ", "")
            values = lecturer[1].reset_index()
            #Format the times to a ["FROM","TO"] list for the current lecturer
            times = [[values["From"][x],values["To"][x]] for x in range(0,len(values["From"]))]
            dates = {}
            #Creates dictionary with all unavailable dates, stored as dictionaries, for the current lecturer
            for x in range(0, len(values["Date"])):
                #We might have two unavailable timeslots during the same day
                if values["Date"][x] in dates:
                    dates[values["Date"][x]].append(times[x])
                else:
                    dates[values["Date"][x]] = [times[x]]

            self.lecturers[name] = dates
        return self.lecturers

    def get_rooms(self):
        return self.rooms.copy()

    def get_courses(self):
        return self.courses.copy()

    def get_lecturers(self):
        return self.lecturers.copy()

    def get_holidays(self):
        return self.holidays.copy()

    def get_period_info(self):
        return self.period_info.copy()

    def get_free_timeslots(self):
        return self.free_timeslots.copy()