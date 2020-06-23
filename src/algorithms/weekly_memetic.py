"""
Weekly Timetable scheduler (based off of the local search algorithm)
===================

author: Huy Ngo
author: Yu Fee Chan
author: Daniel Kaestner & PP :P
author: Paul Disbeschl & PP ;P
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim

sDocumented following PEP 257.
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
from framework.evaluate import Evaluate
from algorithms.tabu import Tabu
import sys
import datetime
import random

class Weekly_memetic(Scheduler):
#    logFile = open(os.path.realpath('./Logs/log.txt'), "a")
    population_size = 10
    tournament_size = 5
    LS_iter_init = 20
    LS_destroy = 2
    prob_mutate = .5
    LS_iter_GA = 10
    GA_iter = 25
    only_local_search = False

    def __init__(self, excel_file_path='./InputOutput/Sample.xlsx'):
#        self.logFile.write('Initialising Weekly algorithm\n')
        super().__init__(excel_file_path)
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
        sched_temp = {t: [] for t in self.timeslots}
        # make a schedule in a greedy way
        for i,event in enumerate(events):
            print("Processing " + event["CourseID"])
            course_info = event["CourseInfo"]
            course_id = event["CourseID"]
            # try to put in first available room-time
            for rt_key, room_time in room_time_avb.items():
                timeslot = room_time["TimeSlot"]
                room_id = room_time["RoomID"]

                
                #Check if the lecturer is already teaching a course at that time
                # if clash, go to next room-time combo
                if self.has_lecturer_conflict(chrom_greedy, courses, timeslot, course_info) or self.has_prog_conflict2(sched_temp, timeslot, course_id, course_info):
                    continue
                
                # remove room-time from the list
                room_time_avb.pop(room_id+"_"+timeslot)
                room_times[room_id].remove(timeslot)
                
                # update chromosome
                chrom_greedy["Gen"+str(i)] = {"CourseID": course_id, "TimeSlot":timeslot, "RoomID":room_id}
                # update schedule
                sched_temp[timeslot].append({'CourseID':course_id, 'Gene_no':"Gen"+str(i),
                                              'ProgID': event['CourseInfo']['Programme'], 'RoomID': room_id})
                break
        return chrom_greedy, room_times
    
        """
    This is a very very hacky brute force algorithm to generate a simple feasible thing """
    def create_random_chrom(self,room_time_avb, room_times):
        chrom = {}
        sched_temp = {t: [] for t in self.timeslots}
        
        # make a schedule in a greedy way
        for i,event in enumerate(self.all_events):
            print("Processing " + event["CourseID"])
            course_info = event["CourseInfo"]
            course_id = event["CourseID"]
            allocated = False
            while not allocated:
                # try to put in first available room-time
                rt_key, room_time = random.choice(list(room_time_avb.items()))
                timeslot = room_time["TimeSlot"]
                room_id = room_time["RoomID"]
                
                #Check if the lecturer is already teaching a course at that time
                # if clash, go to next room-time combo
                if self.has_lecturer_conflict(chrom, self.courses, timeslot, course_info) or self.has_prog_conflict2(sched_temp, timeslot, course_id, course_info):
                    continue
                
                # remove room-time from the list
                allocated = True
                room_time_avb.pop(room_id+"_"+timeslot)
                room_times[room_id].remove(timeslot)
                
                # update chromosome
                chrom["Gen"+str(i)] = {"CourseID": course_id, "TimeSlot":timeslot, "RoomID":room_id}
                sched_temp[timeslot].append({'CourseID':course_id, 'Gene_no':"Gen"+str(i),
                                              'ProgID': event['CourseInfo']['Programme'], 'RoomID': room_id})
                break
        return chrom, room_times
    
    def chrom_to_schedule(self, chrom):
        schedule = {}
        for t in self.timeslots:
            schedule[t] = []
        # translate chromosome into schedule
        for gene_no, gene in chrom.items():
            timeslot = gene["TimeSlot"]
            course_id = gene["CourseID"]
            prog_id = self.courses[gene["CourseID"]]["Programme"]
            room_id = gene["RoomID"]
            schedule[timeslot].append({"CourseID" : course_id
                                    , "ProgID" : prog_id, "RoomID" : room_id,
                                    "Gene_no": gene_no})
        return schedule
    
    def schedule_to_chrom(self, individual):
        chrom = {}
        schedule = individual['Schedule']
        for timeslot, events in schedule.items():
            for i,event in enumerate(events):
                gene_key = event['Gene_no']
                gene = {'CourseID': event['CourseID'],
                        'TimeSlot': timeslot,
                        'RoomID': event['RoomID']}
                chrom[gene_key] = gene
        return chrom
######################## DESTROY & REPAIR OPERATORS ###########################
    def worst_removal(self, individual,q=2):
        q = self.LS_destroy
        p = 6
        score_before = individual['Score']
        # copy of the schedule, such that it is LOCAL!!
        schedule = copy.deepcopy(individual['Schedule'])
        score_diff = []
        removed = []
        while q > 0:
            event_list = []
            delta_scores = []
            for timeslot, events in schedule.items():
                events_copy = copy.deepcopy(events)
                for i,event in enumerate(events_copy):
                    event_copy = copy.deepcopy(event)
                    events.remove(event_copy)
                    delta_score = score_before - self.evaluate(schedule)
                    delta_scores.append(delta_score)
                    events.append(event_copy)
                    event_list.append((timeslot,event_copy))
            
            # find which event to remove
            index_sorted = sorted(range(len(delta_scores)), key=lambda k: delta_scores[k])
            y = np.random.uniform(0,1)
            event_removed = event_list[index_sorted[math.floor(y**p*len(event_list))]]
            removed.append(event_removed)
            score_diff.append(delta_scores[index_sorted[math.floor(y**p*len(event_list))]])
            # remove from schedule copy
            schedule[event_removed[0]].remove(event_removed[1])
            q -= 1
        # update individual
        individual['Schedule'] = schedule
        individual['Score'] = self.evaluate(schedule)
        # r[0] = timeslot, r[1] = event
        for r in removed:
            individual['Availables'][r[1]['RoomID']].append(r[0])
        return removed, individual
    
    def greedy_insertion(self, removed, individual):
        schedule = copy.deepcopy(individual['Schedule'])
        scores_new = []
        insert_locs = []
        for i, event in enumerate(removed):
            scores_new.append([])
            for room_id, timeslots in individual['Availables'].items():
                # if there are available timeslots in the room room_id
                if len(timeslots) > 0:
                    for timeslot in timeslots:
                        if i == 0:
                            insert_locs.append((room_id, timeslot))
                        # check if insertion is viable
                        if not self.has_lecturer_conflict2(schedule, timeslot, event[1]) and not self.has_prog_conflict(schedule, timeslot, event[1]):
                            schedule[timeslot].append(event[1])
                            scores_new[i].append(self.evaluate(schedule))
                            schedule[timeslot].remove(event[1])
                        else:
                            scores_new[i].append(float('inf')*-1)
                        
        scores_new = np.array(scores_new)
        best_scores = np.amax(scores_new,axis=1)
        event_index = np.argmax(best_scores)
        event_insert = removed[event_index][1]
        timeslot_before = removed[event_index][0]
        # new position of the before removed event [0]:room_id, [1]:timeslot
        insert_loc = insert_locs[np.argmax(scores_new[event_index,:])]
#           print("Moved: " + str(timeslot_before) + str(event_insert) + ", To: " + str(insert_loc))
        if self.has_lecturer_conflict2(schedule, insert_loc[1], event_insert):
            print("ERROR")
        elif self.has_prog_conflict(schedule, insert_loc[1], event_insert):
            print("ERROR")
        # change room of event
        event_insert['RoomID'] = insert_loc[0]
        # insert in schedule
        schedule[insert_loc[1]].append(event_insert)
        individual['Schedule'] = schedule
#            individual['Chromosome'][event_insert['Gene_no']] = ({'CourseID': event_insert['CourseID'],
#                      'RoomID': insert_loc[0], 'TimeSlot': insert_loc[1]})
        individual['Availables'][insert_loc[0]].remove(insert_loc[1])
        individual['Score'] = best_scores[event_index] # score update
        removed.remove(removed[event_index])
        return removed, individual
###############################################################################
        
    def local_search(self, individual, num_iter = 10, num_neighbors = 5):
        
        for i in range(num_iter):
            print("LS iteration: " + str(i+1) + "/" +  str(num_iter))
            removed, individual = self.worst_removal(individual)
            while len(removed) > 0:
                removed, individual = self.greedy_insertion(removed, individual)
        individual['Chromosome'] = self.schedule_to_chrom(individual)
        
        return individual
    
    def genetic_alg(self, population, num_iter, prob_mutate):
        ############################ CROSSOVER ################################
        def crossover(population, selection = 'tournament', tournament_size=self.tournament_size):
            candidates = list(population.keys())
            parents = []
                
            # Tournament selection
            if selection == 'tournament':
                while len(parents) < 2:
                    tour_selection = random.sample(candidates, tournament_size)
                    scores = [population[individual]['Score'] for individual in tour_selection]
                    parent = tour_selection[np.argmax(scores)]
                    parents.append(population[parent]['Chromosome'])
                    candidates.remove(parent)
            
            child = {gene: {'CourseID': event['CourseID'], 'TimeSlot': None,
                            'RoomID': None } for gene, event in parents[0].items()}
            
            prgrm_parent_chooser = {prog: None for prog in self.programmes}
            for program in prgrm_parent_chooser.keys():
                prgrm_parent_chooser[program] = round(np.random.uniform(0,1))
                
            course_parent_chooser = {course_code: None for course_code in self.courses.keys()}
            for course_code in course_parent_chooser.keys():
                course_parent_chooser[course_code] = prgrm_parent_chooser[self.courses[course_code]['Programme']]
                
            
            # Perform crossover with the parents 
            for gene, event in child.items():
                if course_parent_chooser[event['CourseID']] == 0:
                    event['TimeSlot'] = parents[0][gene]['TimeSlot']
                else:
                    event['TimeSlot'] = parents[1][gene]['TimeSlot']
            
            _,available_rt = self.get_room_times(self.get_timeslots())
            
            # Allocate rooms to the courses (now: greedy)
            for event in child.values():
                allocated = False
                while not allocated:
                    for room, timeslots in available_rt.items():
                        # check if timeslot in room is available
                        if event['TimeSlot'] in timeslots:
                            event['RoomID'] = room
                            timeslots.remove(event['TimeSlot'])
                            allocated = True
                            break
                    if not allocated:
                        print("ALL ROOMS ARE UNAVAILABLE FOR TIMESLOT")
            return child, available_rt
        #######################################################################
        ############################### MUTATION ##############################
        def mutate(child):
            prog_remove = random.choice(self.programmes)
            print("MUTATE " + prog_remove)
             # copy of the schedule, such that it is LOCAL!!
            schedule = copy.deepcopy(child['Schedule'])
            removed = []
            # remove all courses from chosen program
            for timeslot, events in schedule.items():
                for i,event in enumerate(events):
                    if event['ProgID'] == prog_remove:
                        removed.append((timeslot,events.pop(i)))
            for r in removed:
                child['Availables'][r[1]['RoomID']].append(r[0])
            child['Score'] = self.evaluate(schedule)
            child['Schedule'] = schedule
            
            # re-allocate removed courses with greedy insertion
            while len(removed) > 0:
                removed, child = self.greedy_insertion(removed, child)
            
            return child #mutated!
            
            
        ########################## GENETIC ALG ################################    
        for i in range(num_iter):
            print("GA iteration: " + str(i+1) + "/" + str(num_iter))
            # MAKE CHILD
            child, available_rt = crossover(population)
            schedule = self.chrom_to_schedule(child)
            child = {'Chromosome': child, 'Availables': available_rt, 
                     'Schedule': schedule, 'Score': self.evaluate(schedule)}
            
            # Mutate child with probability prob_mutate
            if np.random.uniform(0,1) < prob_mutate:
                child = mutate(child)
            
            # Perform local search on child
            child = self.local_search(child, self.LS_iter_GA)
            
            # determine worst individual
            worst = None
            worst_score = 9999
            for indiv_num, individual in population.items():
                if individual['Score'] < worst_score:
                    worst = indiv_num
                    worst_score = individual['Score']
            
            # replace worst individual
            print(worst,worst_score)
            population[worst] = child
            
            
            
        return population
            
        
    
    def generate_weekly_timetable(self,weekly_courses):
        #The final json shedule in the format: {BAY1: {Timeslot: CouseID, Timeslot:CourseID}, BAY2:{...}...}
        #Create a clone of the courses that we can manipulate
        self.courses = weekly_courses
        self.all_events, self.programmes = self.get_events_programmes(self.courses)
        
        self.timeslots = self.get_timeslots()
        
        self.times, self.days = self.get_times_days(self.timeslots)
        
        room_time_avb, rooms_times = self.get_room_times(self.timeslots)
        
        print(self.courses)
        
        # a population is a list of chromosomes. Each chromosome represents a 
        # solution
        population = {}     
        # a chromosome is a dictionary with genes, where each gene is a dictionary
        # with {courseID, timeslot, roomID}
        # Initialize one chromosome using greedy algorithm
        chrom,avb = self.create_greedy_chrom(self.all_events, copy.deepcopy(room_time_avb),
                                                    copy.deepcopy(rooms_times), weekly_courses)
        sched = self.chrom_to_schedule(chrom)
        population['Individual 1']= {'Chromosome':chrom, 'Availables': avb, 
                           'Score':self.evaluate(sched), 'Schedule': sched}
        
        if not self.only_local_search:
            # Add random chromosomes
            for i in range(self.population_size - 1):
                chrom, avb = self.create_random_chrom(copy.deepcopy(room_time_avb),
                                                        copy.deepcopy(rooms_times))
                sched = self.chrom_to_schedule(chrom)
                population['Individual ' + str(i+2)] = {'Chromosome':chrom, 'Availables': avb, 
                               'Score':self.evaluate(sched), 'Schedule': sched}
#        
        # Apply local search on every individual 
        for individ_num, individual in population.items():
            print("Local search for " + individ_num)
            individual = self.local_search(individual,self.LS_iter_init)
            individual['Chromosome'] = self.schedule_to_chrom(individual)
        
        if not self.only_local_search:
            # Perform Genetic Algorithm
            population = self.genetic_alg(population, self.GA_iter, self.prob_mutate)
        
        # Choose best individual for final schedule
        best_score = -999
        best_indiv = float('nan')
        
        for individ_num,individual in population.items():
            if individual['Score'] > best_score:
                best_score = individual['Score']
                best_indiv = individ_num
        chrom_final = population[best_indiv]['Chromosome']
        
        schedule_final = population[best_indiv]['Schedule']
        
        # translate chromosome into schedule
        for gene_no, gene in chrom_final.items():
            timeslot = gene["TimeSlot"]
            course_id = gene["CourseID"]
            prog_id = weekly_courses[gene["CourseID"]]["Programme"]
            room_id = gene["RoomID"]
            self.schedule.setdefault(timeslot, []).append({"CourseID" : course_id+
                "("+str(weekly_courses[course_id]['Elective'])+")", "ProgID" : prog_id, "RoomID" : room_id})
                    
        self.copy_schedule(schedule_final)
        
        for individual in population.values():
            print(self.evaluate(individual['Schedule']))
        return population
    
    
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
    
    def has_prog_conflict2(self, schedule, timeslot, course_id, course_info):
        courses = self.hard_constraints.get_courses()
        if timeslot not in schedule.keys():
            return False
        #Iterate over all scheduled courses in a timeslot
        for scheduled_course_info in schedule[timeslot]:
            scheduled_course = courses[scheduled_course_info['CourseID']]
            # Check if the students of the currently 'to-be-planned course' are already in a class (Excluding Electives!)
            if scheduled_course['Programme'] == course_info['Programme']:
                if courses[course_id]['Elective']==0 or scheduled_course['Elective'] == 0:
                    return True
        return False
    
    def has_prog_conflict(self, schedule, timeslot, course):
        courses = self.hard_constraints.get_courses()
        if timeslot not in schedule.keys():
            return False
        #Iterate over all scheduled courses in a timeslot
        for scheduled_course_info in schedule[timeslot]:
            scheduled_course = courses[scheduled_course_info['CourseID']]
            # Check if the students of the currently 'to-be-planned course' are already in a class (Excluding Electives!)
            if scheduled_course['Programme'] == course['ProgID']:
                if courses[course['CourseID']]['Elective']==0 or scheduled_course['Elective'] == 0:
                    return True
        return False

    def has_lecturer_conflict2(self, schedule, timeslot, course):
        courses = self.hard_constraints.get_courses()
        if timeslot not in schedule.keys():
            return False
        #Iterate over all scheduled courses in a timeslot
        for scheduled_course_info in schedule[timeslot]:
            scheduled_course = courses[scheduled_course_info['CourseID']]
            #For each scheduled course in the timeslot, iterate over all lecturers
            for lecturer in scheduled_course['Lecturers'].split(';'):
                # For each scheduled course in the timeslot, check if the lecturer of the current course is already teaching a course
                if lecturer in courses[course['CourseID']]['Lecturers']:
                    return True
        return False
    
    def copy_schedule(self, week_schedule):
        period_end = self.hard_constraints.period_info["EndDate"]
        week_counter = 1
        first_lecture = datetime.datetime.strptime(next(iter(week_schedule.keys())), '%Y-%m-%d %H:%M:%S')
        courses = self.courses
        while first_lecture + timedelta(days= 7 * week_counter) < period_end:
            for date, scheduled_courses in week_schedule.items():
                date_temp = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S') + timedelta(days= 7 * week_counter)

                for course in scheduled_courses:
                    course_id = course["CourseID"]

                    # Check, if the lecturer is already teaching a course at that time
                    if self.has_lecturer_conflict2(self.schedule, str(date_temp), course):
                        continue


                    self.schedule.setdefault(str(date_temp), []).append({"CourseID" : course_id, 
                                            "ProgID" : course["ProgID"], "RoomID" : course["RoomID"]})
                    courses[course_id]['Contact hours'] -= 2
            week_counter += 1
    
    def get_events_programmes(self, weekly_courses):
        # create events for each course: each event is max 2 contact hours
        # events with 1 hour duration still take full timeslot
        all_events = []
        programmes = []
        for course_id, course in weekly_courses.items():
            if course["Programme"] not in programmes:
                programmes.append(course["Programme"])
            for i in range(math.ceil(course["Contact hours"]/2)):
                all_events.append({"CourseID": course_id, "CourseInfo": course})
        return all_events, programmes
                
    def get_timeslots(self):    
        # create dictionary of all timeslots and rooms combinations
        timeslots = copy.deepcopy(self.hard_constraints.get_free_timeslots())[0:20]
        timeslots_str = [str(t) for t in timeslots]
        return timeslots_str
    
    def get_times_days(self, timeslots):
        times = []
        days = []
        for t in timeslots:
            if t[0:10] not in days:
                days.append(t[0:10]) 
            if t[-8:] not in times:
                times.append(t[-8:])
        return times, days
    
    def get_room_times(self, timeslots):
        rooms = self.hard_constraints.get_rooms()
        rooms_times = {}
        rt_avb = {}
        for room_id, room_info in rooms.items():
            rooms_times[room_id] = copy.deepcopy(timeslots)
            for t in timeslots:
                rt_avb[room_id+"_"+t] = {"RoomID":room_id,"TimeSlot":t}
        room_time_avb = copy.deepcopy(rt_avb)
        rooms_times = copy.deepcopy(rooms_times)
        return room_time_avb, rooms_times

    def get_schedule(self):
        return self.schedule
    
    def evaluate(self, schedule):
        """
        Evaluates a schedule assuming that no hard constraint is violated.
        """
        e = Evaluate(schedule, False, True)
        return e.get_score()
