"""
Combine Weekly + Tabu
===================

author: Huy Ngo
author: Yu Fee Chan
author: Daniel Kaestner
author: Paul Disbeschl
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim

Documented following PEP 257.
"""

from framework.scheduler import Scheduler
from algorithms.weekly import Weekly
from algorithms.tabu import Tabu
import datetime


class Weekly_Tabu(Scheduler):

    def __init__(self, excel_file_path='./InputOutput/Sample.xlsx'):
        super().__init__(excel_file_path)
        self.excel_file_path = excel_file_path

    def generate_timetable(self):
        print("Generating weekly schedule")
        # generate schedule for one week
        weekly = Weekly(self.excel_file_path)
        week_timeslots = weekly.generate_timeslots_empty_week()
        weekly_courses = weekly.week_course_splitter()
        week_schedule = weekly.generate_weekly_timetable(weekly_courses, week_timeslots)
        # add unused timeslots so that tabu search can use it
        for timeslot in week_timeslots:
            if timeslot not in week_schedule.keys():
                week_schedule.setdefault(timeslot, [])

        print("Improving weekly schedule using tabu search")
        # generate schedule to be used by tabu search
        initial_week_schedule = {}
        for timeslot in week_schedule:
            initial_week_schedule.setdefault(str(timeslot), week_schedule[timeslot])
        # improve that week using tabu search
        weekly_tabu = Tabu(self.excel_file_path)
        weekly_tabu.total_iterations = 500
        weekly_tabu.generate_timetable(initial_week_schedule)
        tabu_week_schedule = weekly_tabu.get_schedule()

        print("Copy weekly schedule to all weeks in period")
        # back to timestamps
        improved_week_schedule = {}
        for timeslot in tabu_week_schedule:
            improved_week_schedule.setdefault(datetime.datetime.strptime(timeslot, '%Y-%m-%d %H:%M:%S'), tabu_week_schedule[timeslot])
        # copy week and fix all hard constraint violations
        weekly.copy_schedule(improved_week_schedule)
        initial_schedule = weekly.get_schedule()
        self.schedule = initial_schedule

        print("Improve schedule using tabu search")
        # improve complete schedule using tabu search
        tabu = Tabu(self.excel_file_path)
        tabu.total_iterations = 50
        tabu.generate_timetable(initial_schedule)
        self.schedule = tabu.get_schedule()