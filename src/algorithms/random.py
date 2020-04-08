"""
Random Timetable scheduler
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
import json, os
import numpy as np

class Random(Scheduler):
    logFile = open(os.path.realpath('./Logs/log.txt'), "a")

    def __init__(self):
        self.logFile.write('Initialising Random algorithm\n')
        super().__init__()

    def generate_timetable(self, seed=None):
        if seed is None:
            seed = np.random.randint(0,1000000)
            self.logFile.write('Using new generated seed: %i\n' % (seed))
        else:
            self.logFile.write('Using seed: %i\n' % (seed))

        np.random.seed(seed)
        courses = self.hard_constraints.get_courses()
        rooms = self.hard_constraints.get_rooms()

        free_timeslots = self.hard_constraints.get_free_timeslots()
        #print(self.hard_constraints.get_courses())
        #Iterate over all courses
        for course_id, course in courses.items():
            print("Processing " + course_id)
            #Try to put a course into a timeslot and subtract the given contact hourse. Repeat until the course has no contact hours left
            while course['Contact hours'] > 0:
                contact_hours = course['Contact hours']
                #Iterate over all timeslots
                for timeslot in free_timeslots:
                    #Check, if the lecturer is already teaching a course at that time
                    if self.has_lecturer_conflict(courses, timeslot, course):
                        continue

                    #Look for a random free room for the given timeslot
                    room_id = self.find_random_free_room(course, timeslot, rooms.copy())
                    if room_id == None:
                        continue

                    self.schedule.setdefault(timeslot, []).append({"CourseID" : course_id, "RoomID" : room_id})
                    course['Contact hours'] -= 2
                    break

                #If we could not place the course, throw an exception
                if contact_hours == course['Contact hours']:
                    raise Exception('Cannot brute force a schedule for the given constraints')

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


    def find_random_free_room(self, course, timeslot, rooms):
        if timeslot in self.schedule.keys():
            for scheduled_course_info in self.schedule[timeslot]:
                booked_room = scheduled_course_info['RoomID']
                rooms.pop(booked_room)
        valid_rooms = []
        for room in rooms:
            if rooms[room]['Capacity'] > course['Number of students']:
                valid_rooms.append(room)
        if len(valid_rooms)>0:
            return np.random.choice(valid_rooms)
        return None

    def get_schedule(self):
        return self.schedule
