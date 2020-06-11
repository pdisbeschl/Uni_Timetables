"""
Weekly Timetable scheduler (based off of the greedy algorithm)
===================
Just dont look at this code (Paul wrote it)
author: Daniel Kaestner & PP :P
author: Paul Disbeschl & PP ;P
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim
author: Huy Ngo
author: Yu Fee Chan

Documented following PEP 257.
"""
#Assumptions: 36 h per course / 7 = 5.2 hours per course per week
#   Assume Everybody's available
#   Goal - schedule an empty week, place average amount of hours.
#   Copy this week 7 times to make a block and remove infeasabilities.
#   Schedule remaining contact hours.

"""
TODO: 
Consider contact hours when copying from the weekly schedule
Place classes which have conflicts
"""

from framework.scheduler import Scheduler
import json, os
import copy
from datetime import timedelta

class Weekly(Scheduler):
    logFile = open(os.path.realpath('./Logs/log.txt'), "a")

    def __init__(self):
        self.logFile.write('Initialising Weekly algorithm\n')
        super().__init__()



    def generate_timetable(self):
        week_timeslots = self.generate_timeslots_empty_week()
        weekly_courses = self.week_course_splitter()
        week_schedule = self.generate_weekly_timetable(weekly_courses, week_timeslots)
        self.copy_schedule(week_schedule)
    """ 
    The holidays are lists with binary integer variables (key - value pair), indicating if it's a holiday or not
    """
    def generate_timeslots_empty_week(self):  #Generate empty week, starting from the first week
        free_timeslots = []
        weekly_start_date = self.hard_constraints.period_info["StartDate"]  - timedelta(days = 7)# Dromedarycase
        #weekly_end_date = weekly_start_date + timedelta(days=5)
        for j in range(0, 5):
            for i in range(0, 4):
                hour = int(8 + 2 * i + (((i + 1) * 30) / 60))
                start = weekly_start_date.replace(hour=hour, minute=((30 + i * 30) % 60))
                free_timeslots.append(start)
            weekly_start_date = weekly_start_date + timedelta(days=1)
        return free_timeslots

    """ 
    The following method divides the PERIOD by the number of weeks (usually 7), excludes the exam week, converts to int
    Assumption: Block starts on a Monday, ends on a Friday (the dividing by 7 is for the 7 days in a week)
    """
    def week_course_splitter(self):
        weekly_courses = copy.deepcopy(self.hard_constraints.get_courses())
        period_start_date = self.hard_constraints.period_info["StartDate"]
        period_end_date = self.hard_constraints.period_info["EndDate"]
        period_duration = int((period_end_date - period_start_date).days / 7)
        for course_id, course in weekly_courses.items():
            print("Processing " + course_id)
            weekly_courses[course_id]['Contact hours'] = int(course['Contact hours']/period_duration)
        return weekly_courses


    """
    This is a very very hacky brute force algorithm to generate a simple feasible thing """
    def generate_weekly_timetable(self, weekly_courses, week_timeslots):
        week_schedule = {}
        #The final json shedule in the format: {BAY1: {Timeslot: CouseID, Timeslot:CourseID}, BAY2:{...}...}
        #Create a clone of the courses that we can manipulate
        rooms = self.hard_constraints.get_rooms()

        #print(self.hard_constraints.get_courses())
        #Iterate over all courses 
        for course_id, course in weekly_courses.items():
            print("Processing " + course_id)
            prog_id = course['Programme']
            #Try to put a course into a timeslot and subtract the given contact hourse. Repeat until the course has no contact hours left
            while course['Contact hours'] > 0:
                contact_hours = course['Contact hours']
                #Iterate over all timeslots
                for timeslot in week_timeslots:
                    #Check if the programme (year group) isn't already in another class
                    if self.has_prog_conflict(week_schedule, weekly_courses, timeslot, course):
                        continue

                    #Check, if the lecturer is already teaching a course at that time
                    if self.has_lecturer_conflict(week_schedule, weekly_courses, timeslot, course):
                        continue

                    #Look for a free room for the given timeslot
                    room_id = self.find_free_room(week_schedule, course, timeslot, rooms.copy())
                    if room_id == None:
                        continue

                    week_schedule.setdefault(timeslot, []).append({"CourseID" : course_id, "ProgID" : prog_id, "RoomID" : room_id})
                    course['Contact hours'] -= 2
                    break

                #If we could not place the course, throw an exception
                if contact_hours == course['Contact hours']:
                    raise Exception('Cannot brute force a schedule for the given constraints')
        return week_schedule

    """
    Copy the schedule, generated for the empty week to the total weeks of the period, while preserving the contact hours 
    which could not be scheduled (e.g. due to an overlap)
    """
    def copy_schedule(self, week_schedule):
        period_end = self.hard_constraints.period_info["EndDate"]
        week_counter = 1
        first_lecture = next(iter(week_schedule.keys()))
        courses = self.hard_constraints.get_courses()
        while first_lecture + timedelta(days= 7 * week_counter) < period_end:
            for date, scheduled_courses in week_schedule.items():
                date = date + timedelta(days= 7 * week_counter)

                for course in scheduled_courses:
                    course_id = course["CourseID"]

                    # Check, if the lecturer is already teaching a course at that time
                    if self.has_lecturer_conflict(self.schedule, courses, date, courses[course_id]):
                        continue


                    self.schedule.setdefault(date, []).append({"CourseID" : course_id, "ProgID" : course["ProgID"], "RoomID" : course["RoomID"]})
                    courses[course_id]['Contact hours'] -= 2
            week_counter += 1

    """
    The following method checks to see if there is no conflict between classes of the same programme (year-group).
    Idea: Programmes can't be scheduled at the same time unless the classes are electives.
    """
    def has_prog_conflict(self, week_schedule, courses, timeslot, course):
        if timeslot not in week_schedule.keys():
            return False
        #Iterate over all scheduled courses in a timeslot
        for scheduled_course_info in week_schedule[timeslot]:
            scheduled_course = courses[scheduled_course_info['CourseID']]
            # Check if the students of the currently 'to-be-planned course' are already in a class (Excluding Electives!)
            if scheduled_course['Programme'] == course['Programme']:
                if course['Elective']==0:
                    return True
        return False

    def has_lecturer_conflict(self, schedule, courses, timeslot, course):
        #Check if any of the lecturers which teach the course is on holiday on the current day
        lecturer_unavailability = self.hard_constraints.get_lecturers()
        for lecturer in course['Lecturers'].split(';'):
            if lecturer in lecturer_unavailability:
                for time in lecturer_unavailability[lecturer]:
                    if time.replace(hour=0, minute=0) == timeslot.replace(hour=0, minute=0):
                        return True

        if timeslot not in schedule.keys():
            return False
        #Iterate over all scheduled courses in a timeslot
        for scheduled_course_info in schedule[timeslot]:
            scheduled_course = courses[scheduled_course_info['CourseID']]
            #For each scheduled course in the timeslot, iterate over all lecturers
                # For each scheduled course in the timeslot, check if the lecturer of the current course is already teaching a course
            for lecturer in scheduled_course['Lecturers'].split(';'):
                if lecturer in course['Lecturers']:
                    return True

        return False

    def find_free_room(self, week_schedule, course, timeslot, rooms):
        if timeslot in week_schedule.keys():
            for scheduled_course_info in week_schedule[timeslot]:
                booked_room = scheduled_course_info['RoomID']
                rooms.pop(booked_room)
        for room in rooms:
            if rooms[room]['Capacity'] > course['Number of students']:
                return room
        return None
