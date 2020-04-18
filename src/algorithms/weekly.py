"""
Weekly Timetable scheduler (based off of the greedy algorithm)
===================

author: Huy Ngo
author: Yu Fee Chan
author: Daniel Kaestner & PP :P
author: Paul Disbeschl & PP ;P
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim

Documented following PEP 257.
"""
#Assumptions: 36 h per course / 7 = 5.2 hours per course per week
#   Assume Everybody's available
#   Goal - schedule an empty week, place average amount of hours.
#   Copy this week 7 times to make a block and remove infeasabilities.
#   Schedule remaining contact hours.

from framework.scheduler import Scheduler
import json, os
from datetime import timedelta

class Weekly(Scheduler):
    logFile = open(os.path.realpath('./Logs/log.txt'), "a")

    def __init__(self):
        self.logFile.write('Initialising Weekly algorithm\n')
        super().__init__()
        self.generate_empty_timeslots()

    def schedule_empty_week(self):
        free_timeslots = self.hard_constraints.get_free_timeslots()
        weekly_contact_hours = self.hard_constraints.get_courses()
        weekly_contact_hours = +7

    """ 
    The holidays are lists with binary integer variables (key - value pair), indicating if it's a holiday or not
    """
    def generate_empty_timeslots(self):  #Generate empty week, starting from the first week
        free_timeslots = []
        weekly_start_date = self.hard_constraints.period_info["StartDate"]  # Dromedarycase
        #weekly_end_date = weekly_start_date + timedelta(days=5)
        for j in range(0, 5):
            for i in range(0, 4):
                hour = int(8 + 2 * i + (((i + 1) * 30) / 60))
                start = weekly_start_date.replace(hour=hour, minute=((30 + i * 30) % 60))
                free_timeslots.append(str(start))
            weekly_start_date = weekly_start_date + timedelta(days=1)
        return free_timeslots

    def generate_timetable(self):
        weekly_courses = self.week_course_splitter()
        self.generate_weekly_timetable(weekly_courses)

    """ 
    The following method divides the PERIOD by the number of weeks (usually 7), excludes the exam week, converts to int
    Assumption: Block starts on a Monday, ends on a Friday (the dividing by 7 is for the 7 days in a week)
    """
    def week_course_splitter(self):
        weekly_courses = self.hard_constraints.get_courses()
        period_start_date = self.hard_constraints.period_info["StartDate"]
        period_end_date = self.hard_constraints.period_info["EndDate"]
        period_duration = int((period_end_date - period_start_date).days / 7)
        for course_id, course in weekly_courses.items():
            print("Processing " + course_id)
            course['Contact hours'] = int(course['Contact hours']/period_duration)
        return weekly_courses

    """
    This is a very very hacky brute force algorithm to generate a simple feasible thing """
    def generate_weekly_timetable(self,weekly_courses):
        #The final json shedule in the format: {BAY1: {Timeslot: CouseID, Timeslot:CourseID}, BAY2:{...}...}
        #Create a clone of the courses that we can manipulate
        rooms = self.hard_constraints.get_rooms()

        free_timeslots = self.hard_constraints.get_free_timeslots()
        #print(self.hard_constraints.get_courses())
        #Iterate over all courses
        for course_id, course in weekly_courses.items():
            print("Processing " + course_id)
            prog_id = course['Programme']
            #Try to put a course into a timeslot and subtract the given contact hourse. Repeat until the course has no contact hours left
            while course['Contact hours'] > 0:
                contact_hours = course['Contact hours']
                #Iterate over all timeslots
                for timeslot in free_timeslots:
                    #Check if the programme (year group) isn't already in another class
                    if self.has_prog_conflict(weekly_courses, timeslot, course):
                        continue

                    #Check, if the lecturer is already teaching a course at that time
                    if self.has_lecturer_conflict(weekly_courses, timeslot, course):
                        continue


                    #Look for a free room for the given timeslot
                    room_id = self.find_free_room(course, timeslot, rooms.copy())
                    if room_id == None:
                        continue

                    self.schedule.setdefault(timeslot, []).append({"CourseID" : course_id, "ProgID" : prog_id, "RoomID" : room_id})
                    course['Contact hours'] -= 2
                    break

                #If we could not place the course, throw an exception
                if contact_hours == course['Contact hours']:
                    raise Exception('Cannot brute force a schedule for the given constraints')

    """
    The following method checks to see if there is no conflict between classes of the same programme (year-group).
    Idea: Programmes can't be scheduled at the same time unless the classes are electives.
    """
    def has_prog_conflict(self, courses, timeslot, course):
        if timeslot not in self.schedule.keys():
            return False
        #Iterate over all scheduled courses in a timeslot
        for scheduled_course_info in self.schedule[timeslot]:
            scheduled_course = courses[scheduled_course_info['CourseID']]
            # Check if the students of the currently 'to-be-planned course' are already in a class (Excluding Electives!)
            if scheduled_course['Programme'] == course['Programme']:
                if course['Elective']==0:
                    return True
        return False

    def has_lecturer_conflict(self, courses, timeslot, course):
        if timeslot not in self.schedule.keys():
            return False
        #Iterate over all scheduled courses in a timeslot
        for scheduled_course_info in self.schedule[timeslot]:
            scheduled_course = courses[scheduled_course_info['CourseID']]
            #For each scheduled course in the timeslot, iterate over all lecturers
            for lecturer in scheduled_course['Lecturers'].split(';'):
                # For each scheduled course in the timeslot, check if the lecturer of the current course is already teaching a course
                if lecturer in course['Lecturers']:
                    return True
        return False

    def find_free_room(self, course, timeslot, rooms):
        if timeslot in self.schedule.keys():
            for scheduled_course_info in self.schedule[timeslot]:
                booked_room = scheduled_course_info['RoomID']
                rooms.pop(booked_room)
        for room in rooms:
            if rooms[room]['Capacity'] > course['Number of students']:
                return room
        return None

    def get_schedule(self):
        return self.schedule
