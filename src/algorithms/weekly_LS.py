"""
Weekly Timetable scheduler (based off of the local search algorithm)
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
import math
import copy

class Weekly_LS(Scheduler):
#    logFile = open(os.path.realpath('./Logs/log.txt'), "a")

    def __init__(self):
#        self.logFile.write('Initialising Weekly algorithm\n')
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
    def create_greedy_chrom(self, events, room_time_avb, courses):
        chrom_greedy = {}
        
        # make a schedule in a greedy way
        for i,event in enumerate(events):
            print("Processing " + event["CourseID"])
            prog_id = event["CourseInfo"]["Programme"]
            course = event["CourseInfo"]
            course_id = event["CourseID"]
            # try to put in first available room-time
            for rt_key, room_time in room_time_avb.items():
                timeslot = room_time["TimeSlot"]
                room_id = room_time["RoomID"]

                
                #Check if the lecturer is already teaching a course at that time
                # if clash, go to next room-time combo
                if self.has_lecturer_conflict(chrom_greedy, courses, timeslot, course):
                    continue
                
                # remove room-time from the list
                room_time_avb.pop(room_id+"_"+timeslot)
                
                # update chromosome
                chrom_greedy["Gen"+str(i)] = {"CourseID": course_id, "TimeSlot":timeslot, "RoomID":room_id}
                break
        return chrom_greedy
            
    
    def generate_weekly_timetable(self,weekly_courses):
        #The final json shedule in the format: {BAY1: {Timeslot: CouseID, Timeslot:CourseID}, BAY2:{...}...}
        #Create a clone of the courses that we can manipulate
        
        
        # create events for each course: each event is max 2 contact hours
        # events with 1 hour duration still take full timeslot
        events = []
        programmes = []
        for course_id, course in weekly_courses.items():
            if course["Programme"] not in programmes:
                programmes.append(course["Programme"])
            for i in range(math.ceil(course["Contact hours"]/2)):
                events.append({"CourseID": course_id, "CourseInfo": course})
                
        
        # create dictionary of all timeslots and rooms combinations
        timeslots = copy.deepcopy(self.hard_constraints.get_free_timeslots())[0:20]
        times = []
        days = []
        for t in timeslots:
            if t[0:10] not in days:
                days.append(t[0:10]) 
            if t[-8:] not in times:
                times.append(t[-8:])
        rooms = self.hard_constraints.get_rooms()
        rt_avb = {}
        for room_id, room_info in rooms.items():
            for t in timeslots:
                rt_avb[room_id+"_"+t] = {"RoomID":room_id,"TimeSlot":t}
        room_time_avb = copy.deepcopy(rt_avb)
        
        # a population is a list of chromosomes. Each chromosome represents a 
        # solution
        population = []        
        # a chromosome is a dictionary with genes, where each gene is a dictionary
        # with {courseID, timeslot, roomID}
        chrom_greedy = self.create_greedy_chrom(events, room_time_avb, weekly_courses)
        population.append(chrom_greedy)    
        
        
        
        chrom_final = chrom_greedy 
        # translate chromosome into schedule
        for gene_no, gene in chrom_final.items():
            timeslot = gene["TimeSlot"]
            course_id = gene["CourseID"]
            prog_id = weekly_courses[gene["CourseID"]]["Programme"]
            room_id = gene["RoomID"]
            self.schedule.setdefault(timeslot, []).append({"CourseID" : course_id+
                "("+str(weekly_courses[course_id]['Elective'])+")", "ProgID" : prog_id, "RoomID" : room_id})

        
    """
    Creates a schedule per program: per day and per timeslot will be either empty
    or a scheduled course
    """
    def schedules_per_program(self, chrom, courses, days, times, programmes):
        schedules = {}
        for programme in programmes:
            schedules[programme] = {}
            for day in days:
                schedules[programme][day] = {}
                for time in times:
                    schedules[programme][day][time] = None
            
            for gene_no, gene in chrom.items():
                if courses[gene["CourseID"]]["Programme"] == programme:
                    schedules[programme][gene["TimeSlot"][0:10]][gene["TimeSlot"][-8:]] = gene
        return schedules
    ########################### HARD CONSTRAINTS ##############################
    """
    Hard constraint 1: lecturer can only give one class per timeslot
    Returns true if violated
    """
    def has_lecturer_conflict(self, chrom, courses, timeslot, course):
        # Iterate over all genes in chromosome
        for gene_no, gene in chrom.items():
            # check if the scheduled course is same timeslot as the triple
            if timeslot == gene["TimeSlot"]:
                scheduled_course = courses[gene["CourseID"]]
                for lecturer in scheduled_course['Lecturers'].split(';'):
                    if lecturer in course['Lecturers']:
                        return True
        return False
    ########################### SOFT CONSTRAINTS ##############################
    """
    Soft constraint 1: Total number of contact hours on a day must not exceed 4?
    Returns true if violated
    """
    def exceeds_max_hours(self, schedules, max_contact_hours, courses):
        # check for each day and each programme if there are more than max_contact_hours
        penalty_counter = 0
        for program, schedule in schedules.items():
            # look for each day if there is a violation
            for day, day_schedule in schedule.items():
                contact_hours = 0
                elective_counter = {}
                for time, event in day_schedule.items():                        
                    if event is not None:
                        if event["CourseID"] not in elective_counter.keys() and courses[event["CourseID"]]["Elective"] == 1:
                            elective_counter[event["CourseID"]] = 0
                        # update hour counter if compulsory course
                        if courses[event["CourseID"]]["Elective"] == 0:
                            contact_hours += 2
                        else:
                            elective_counter[event["CourseID"]] += 2
                            
                # can only do this if there are scheduled electives on this day:
                # contact hours of compulsory + max num. of hours scheduled electives
                if bool(elective_counter):
                    contact_hours = contact_hours + max(list(elective_counter.values()))
                    
                # update penalty counter if it exceeds maximum contact hours
                if contact_hours > max_contact_hours:
                    penalty_counter += 1
                    #print("program:" + program + ", violation on day:" + day)
                
                
            
    
                



    def get_schedule(self):
        return self.schedule
