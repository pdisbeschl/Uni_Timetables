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
import numpy as np
import random

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
    def create_greedy_chrom(self, events, room_time_avb, room_times, courses):
        chrom_greedy = {}
        
        # make a schedule in a greedy way
        for i,event in enumerate(events):
            print("Processing " + event["CourseID"])
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
                room_times[room_id].remove(timeslot)
                
                # update chromosome
                chrom_greedy["Gen"+str(i)] = {"CourseID": course_id, "TimeSlot":timeslot, "RoomID":room_id}
                break
        return chrom_greedy, room_times
    
        """
    This is a very very hacky brute force algorithm to generate a simple feasible thing """
    def create_random_chrom(self, events, room_time_avb, room_times, courses):
        chrom = {}
        
        # make a schedule in a greedy way
        for i,event in enumerate(events):
            print("Processing " + event["CourseID"])
            course = event["CourseInfo"]
            course_id = event["CourseID"]
            allocated = False
            while not allocated:
                # try to put in first available room-time
                rt_key, room_time = random.choice(list(room_time_avb.items()))
                timeslot = room_time["TimeSlot"]
                room_id = room_time["RoomID"]
                
                #Check if the lecturer is already teaching a course at that time
                # if clash, go to next room-time combo
                if self.has_lecturer_conflict(chrom, courses, timeslot, course):
                    continue
                
                # remove room-time from the list
                allocated = True
                room_time_avb.pop(room_id+"_"+timeslot)
                room_times[room_id].remove(timeslot)
                
                # update chromosome
                chrom["Gen"+str(i)] = {"CourseID": course_id, "TimeSlot":timeslot, "RoomID":room_id}
                break
        return chrom, room_times
    
    def chrom_to_schedule(self, chrom, timeslots, courses):
        schedule = {}
        for t in timeslots:
            schedule[t] = []
        # translate chromosome into schedule
        for gene_no, gene in chrom.items():
            timeslot = gene["TimeSlot"]
            course_id = gene["CourseID"]
            prog_id = courses[gene["CourseID"]]["Programme"]
            room_id = gene["RoomID"]
            schedule[timeslot].append({"CourseID" : course_id
                                    , "ProgID" : prog_id, "RoomID" : room_id,
                                    "Gene_no": gene_no})
        return schedule
    
    def local_search(self, individual, num_iter = 100):
        def worst_removal(individual,q=1):
            p = 6
            cost_before = individual['Score']
            # copy of the schedule, such that it is LOCAL!!
            schedule = copy.deepcopy(individual['Schedule'])
            cost_diff = []
            removed = []
            while q > 0:
                event_list = []
                delta_costs = []
                for timeslot, events in schedule.items():
                    events_copy = copy.deepcopy(events)
                    for i,event in enumerate(events_copy):
                        event_copy = copy.deepcopy(event)
                        events.remove(event_copy)
                        delta_cost = np.random.uniform(0,1) ############
                        delta_costs.append(delta_cost)
                        events.append(event_copy)
                        event_list.append((timeslot,event_copy))
                
                # find which event to remove
                index_sorted = sorted(range(len(delta_costs)), key=lambda k: delta_costs[k])
                y = np.random.uniform(0,1)
                event_removed = event_list[index_sorted[math.floor(y**p*len(event_list))]]
                removed.append(event_removed)
                cost_diff.append(delta_costs[index_sorted[math.floor(y**p*len(event_list))]])
                # remove from schedule copy
                schedule[event_removed[0]].remove(event_removed[1])
                q -= 1
            # update individual
            individual['Schedule'] = schedule
            individual['Score'] = cost_before - sum(cost_diff) #######
            # r[0] = timeslot, r[1] = event
            for r in removed:
                individual['Chromosome'][r[1]['Gene_no']] = None
                individual['Availables'][r[1]['RoomID']].append(r[0])
            return removed, individual
        
        def greedy_insertion(removed, individual):
            schedule = copy.deepcopy(individual['Schedule'])
            cost_before = individual['Score']
            cost_diff = []
            insert_locs = []
            for i in range(len(removed)):
                cost_diff.append([])
                for room_id, timeslots in individual['Availables'].items():
                    if len(timeslots) > 0:
                        for timeslot in timeslots:
                            if i == 0:
                                insert_locs.append((room_id, timeslot))
                            schedule[timeslot].append(removed[i][1])
                            cost_diff[i].append(999 - cost_before) ################
                            schedule[timeslot].remove(removed[i][1])
            cost_diff = np.array(cost_diff)
            min_costs = np.amin(cost_diff,axis=1)
            event_index = np.argmin(min_costs)
            event_insert = removed[event_index][1]
            # new position of the before removed event [0]:room_id, [1]:timeslot
            insert_loc = insert_locs[np.argmin(cost_diff[event_index,:])]
            # change room of event
            event_insert['RoomID'] = insert_loc[0]
            # insert in schedule
            schedule[insert_loc[1]].append(event_insert)
            individual['Schedule'] = schedule
            individual['Chromosome'][event_insert['Gene_no']] = ({'CourseID': event_insert['CourseID'],
                      'RoomID': insert_loc[0], 'TimeSlot': insert_loc[1]})
            individual['Availables'][insert_loc[0]].remove(insert_loc[1])
            individual['Score'] += min_costs[event_index] # cost update
            removed.remove(removed[event_index])
            return removed, individual
        
        for i in range(num_iter):
            removed, individual_r = worst_removal(individual, 2)
            while len(removed) > 0:
                removed, individual_r = greedy_insertion(removed, individual_r)
            
        return individual_r
            
        
        
    
    def generate_weekly_timetable(self,weekly_courses):
        #The final json shedule in the format: {BAY1: {Timeslot: CouseID, Timeslot:CourseID}, BAY2:{...}...}
        #Create a clone of the courses that we can manipulate
        
        
        # create events for each course: each event is max 2 contact hours
        # events with 1 hour duration still take full timeslot
        all_events = []
        programmes = []
        for course_id, course in weekly_courses.items():
            if course["Programme"] not in programmes:
                programmes.append(course["Programme"])
            for i in range(math.ceil(course["Contact hours"]/2)):
                all_events.append({"CourseID": course_id, "CourseInfo": course})
                
        
        # create dictionary of all timeslots and rooms combinations
        timeslots = copy.deepcopy(self.hard_constraints.get_free_timeslots())[0:20]
        timeslots_str = [str(t) for t in timeslots]
        timeslots = timeslots_str
        times = []
        days = []
        for t in timeslots:
            if t[0:10] not in days:
                days.append(t[0:10]) 
            if t[-8:] not in times:
                times.append(t[-8:])
        rooms = self.hard_constraints.get_rooms()
        rooms_times = {}
        rt_avb = {}
        for room_id, room_info in rooms.items():
            rooms_times[room_id] = copy.deepcopy(timeslots)
            for t in timeslots:
                rt_avb[room_id+"_"+t] = {"RoomID":room_id,"TimeSlot":t}
        room_time_avb = copy.deepcopy(rt_avb)
        
        # a population is a list of chromosomes. Each chromosome represents a 
        # solution
        population = []        
        # a chromosome is a dictionary with genes, where each gene is a dictionary
        # with {courseID, timeslot, roomID}
        chrom,avb = self.create_greedy_chrom(all_events, copy.deepcopy(room_time_avb),
                                                    copy.deepcopy(rooms_times), weekly_courses)
        sched = self.chrom_to_schedule(chrom, timeslots, weekly_courses)
        population.append({'Chromosome':chrom, 'Availables': avb, 
                           'Score':float('nan'), 'Schedule': sched})
        for i in range(39):
            chrom, avb = self.create_random_chrom(all_events, copy.deepcopy(room_time_avb),
                                                    copy.deepcopy(rooms_times), weekly_courses)
            sched = self.chrom_to_schedule(chrom, timeslots, weekly_courses)
            population.append({'Chromosome':chrom, 'Availables': avb, 
                           'Score':float('nan'), 'Schedule': sched})
    
        individual = population[0]
        individual = self.local_search(individual)
        
        
        
        chrom_final = individual['Chromosome']
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
