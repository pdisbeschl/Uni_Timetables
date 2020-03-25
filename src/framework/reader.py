"""
This class is supposed to process constraints and to transform them into
an uniform way which all the algorithms can read
author: Huy Ngo
author: Yu Fee Chan
author: Daniel Kaestner
author: Paul Disbeschl
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim

Documented following PEP 257.
"""

import pandas as pd

class ConstraintParser():

    def __init__(self):
        #Dictionaries with information about the period, holidays, courses, rooms and lecturers
        self.period_info = {}
        self.courses = {}
        self.rooms = {}
        self.lecturers = {}
        self.holidays = {}
        self.read_excel()

    def read_excel(self):
        #Load the excel file and transform them into dictionaries which we can use for the algorithms
        xls = pd.ExcelFile(__file__ + "//..//..//InputOutput//Sample.xlsx")
        courses_df = pd.read_excel(xls, 'Courses')
        rooms_df = pd.read_excel(xls, 'Rooms')
        holidays_df = pd.read_excel(xls, 'Holidays')
        period_info_df = pd.read_excel(xls, 'PeriodInfo')
        lecturers_df = pd.read_excel(xls, 'Lecturers')

        #Create a dictionary with the shape {CourseID : {Programme: BAY1, ...}} and likewise for all the other files
        self.courses = courses_df.set_index("CourseID").transpose().to_dict()
        self.rooms = rooms_df.set_index("RoomID").transpose().to_dict()
        self.holidays = holidays_df.transpose().to_dict()
        self.period_info = period_info_df.transpose().to_dict()

        #Group unavailabilities for each lecturer
        for lecturer in lecturers_df.groupby("Lecturer"):
            name = lecturer[0]
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

    def get_rooms(self):
        return self.rooms

    def get_courses(self):
        return self.courses

    def get_lecturers(self):
        return self.lecturers

    def get_holidays(self):
        return self.holidays

    def get_period_info(self):
        return self.period_info