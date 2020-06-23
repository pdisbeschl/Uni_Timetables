"""
Greedy Timetable scheduler
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
import json, os, copy

class Greedy(Scheduler):
    logFile = open(os.path.realpath('./Logs/log.txt'), "a")

    def __init__(self):
        self.logFile.write('Initialising Greedy algorithm\n')
        super().__init__()

    """
    This is a very very hacky brute force algorithm to generate a simple feasible schedule"""
    def generate_timetable(self):
        #The final json schedule in the format: {BAY1: {Timeslot: CourseID, Timeslot:CourseID}, BAY2:{...}...}
        #Create a clone of the courses that we can manipulate
        courses = self.hard_constraints.get_courses()
        rooms = self.hard_constraints.get_rooms()

        free_timeslots = self.hard_constraints.get_free_timeslots()
        #print(self.hard_constraints.get_courses())
        project_constraints = 1
        block = 1
        #If project constraint on, apply these changes to the available timeslots and courses to be scheduled. These are semi-hardcoded in since these are irregular and very specific to each period and year group.
        if project_constraints:
            #Copy projects from courses and remove the teaching hours that need to be scheduled in courses below.
            projects = copy.deepcopy(dict(filter(lambda item: item[0].endswith(('300', '600')), courses.items()))) #,'KEN4130','KEN4131','KEN4230','KEN4231' #--> Master projects are not really counted here
            for overlap in projects: courses[overlap]['Contact hours'] = 0

            project_days = {'BAY1': {"Timestamps" : list(filter(lambda item: item.week == free_timeslots[-1].week - 2, free_timeslots))},'BAY2': {"Timestamps" : list(filter(lambda item: (item.weekday() == (1) or item.weekday() == (2)), free_timeslots))},'BAY3': {"Timestamps" : list(filter(lambda item: (item.weekday() == (2) or item.weekday() == (3)), free_timeslots))}}
            if block%3!=1: project_days['BAY1'] = {"Timestamps" : list(filter(lambda item: (item.weekday() == (1) or item.weekday() == (4)), free_timeslots))}
            #Iterate over all Bachelor projects, then iterate over all timeslots reserved for these.
            for project_id, project in projects.items():
                for timeslot in project_days[project["Programme"]]["Timestamps"]:
                    contact_hours = project['Contact hours']
                    #If there are still project meetings to be held (contact hours) - these will be scheduled.
                    if project['Contact hours'] > 0:
                        # Check if the lecturer is already teaching a project at that time
                        if self.has_lecturer_conflict(projects, timeslot, project):
                            continue
                        #Look for a free (meeting) room for the given timeslot
                        room_id = self.find_free_room(project, timeslot, rooms.copy())
                        if room_id != None:
                            self.schedule.setdefault(timeslot, []).append({"CourseID": project_id, "Name": courses[project_id]['Course name'],"ProgID": project['Programme'], "RoomID": room_id, "Lecturers": courses[project_id]['Lecturers']})
                            project['Contact hours'] -= 2
                    #Students have certain days off to work on the project. Staff does not work at this time, and students are not allocated a room to work in. Hence '-1' and 'dummy'.
                    else: self.schedule.setdefault(timeslot, []).append({"CourseID": project_id, "Name": courses[project_id]['Course name'],"ProgID": project['Programme'], "RoomID": '-1', "Lecturers": 'dummy'})

#
        #Iterate over all courses
        for course_id, course in courses.items():
            print("Processing " + course_id)
            prog_id = course['Programme']
            #Try to put a course into a timeslot and subtract the given contact hourse. Repeat until the course has no contact hours left
            while course['Contact hours'] > 0:
                contact_hours = course['Contact hours']
                #Iterate over all timeslots
                for timeslot in free_timeslots:
                    #Check if the programme (year group) isn't already in another class
                    if self.has_prog_conflict(courses, timeslot, course):
                        continue

                    #Check if the lecturer is already teaching a course at that time
                    if self.has_lecturer_conflict(courses, timeslot, course):
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
                rooms.pop(booked_room,-1)
        for room in rooms:
            if rooms[room]['Capacity'] > course['Number of students']:
                return room
        return None

