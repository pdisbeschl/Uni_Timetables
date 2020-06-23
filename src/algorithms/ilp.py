"""
ILP Timetable scheduler
===================

author: Huy Ngo
author: Yu Fee Chan
author: Daniel Kaestner
author: Paul Disbeschl
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim

Documented following PEP 257.
"""
import os
from mip import *
from framework.scheduler import Scheduler
import datetime
import json
"""
A class to build a schedule computed bz an ILP
"""
class ILP(Scheduler):
    logFile = open(os.path.realpath('./Logs/log.txt'), "a")

    def __init__(self):
        super().__init__()
        metrics_file_path = "framework/evaluation_metrics.json"
        with open(os.path.realpath(metrics_file_path), "r") as f:
            self.metrics = json.load(f)

        #Create the ILP model
        self.model = Model(sense=MINIMIZE, solver_name=CBC)
        #Supresses output from the ILP
        self.model.verbose = 0
        self.model.threads = -1

    """
    Method which is called to generate the timetable
    """
    def generate_timetable(self):
        self.generate_ILP_hard_constraints()
        self.tranform_to_schedule()
        return

    """
    Set up the basic structure of the ILP 
    The objective function is (as of now) useless because we onlz have hard constraints and no proper evaluation. Later the 
    objective function will evaluate the soft constraints (e.g. score for lectures at 8:30 will have a high cost) 
    Create binary decision variables for every course,timeslot combination (if 1 then the course is scheduled in the timeslot)
    Ensure that every course is scheduled for the amount of contact hours
    """
    def generate_ILP_hard_constraints(self):
        self.free_timeslots = self.hard_constraints.get_free_timeslots()
        self.courses = self.hard_constraints.get_courses()
        #Get a list of all the courses taught by a lecturer
        lecturers = self.get_course_list_of_lecturer()

        #Define binary decision variables for every course and timeslot. If the variable is 1 it means that the course
        # is scheduled at the timeslot
        x = [self.model.add_var(var_type=BINARY, name=str(tid)+";"+cid)for cid in self.courses.keys() for tid in self.free_timeslots]

        #Temporary objective function. It pretty much does nothing useful at the moment. Just adds all courses and timeslots
        #together
        #self.model.objective = maximize(xsum(1 * self.model.var_by_name(str(tid)+";"+cid) for cid in self.courses.keys() for tid in self.free_timeslots))

        self.repetitiveness_score()

        self.lecture_start_score(x)

        #Add all constraints to the ILP
        #Ensure that every course is taught exactly the required hours
        self.add_contact_hours_constraint()
        #Ensure that two courses of the same year do not fall on the same timeslot
        self.add_no_course_overlap_constraint()
        #Ensure that noone has to teach two courses at the same time
        self.add_lecturer_overlap_constraint(lecturers)
        #Ensure that noone has to teach when he is not available
        self.add_unavailability_constraints(lecturers)



        #self.model.write('model.lp')
        ##################################################################################################################
        ##########################NO MORE CONSTRAINTS OR VARIABLES AFTER THIS#############################################
        ##################################################################################################################
        #Solve the ILP
        #self.model.seed = int(time.time())
        #self.model.max_mip_gap = 5
        #self.model.integer_tol = 0.25
        #self.model.max_mip_gap_abs = 5
        status = self.model.optimize(max_seconds=10)
        #Get all timeslot,course tuples which are scheduled
        self.selected = [x[i].name for i in range(len(x)) if x[i].x >= 0.9]
        #Sort the solution by timeslots
        self.selected.sort()

    """
    Add a score for each lecture based on the starting time of the lecture. The score is taken from the evaluation_metrics.json
    Which derrives the scoring from the survey that was performed
    """
    def lecture_start_score(self, x):
        lecture_start = [[],[],[]]
        start_score = self.metrics['preferences']['starting_time']
        multiplier = [0] * len(start_score)
        for index, score in enumerate(start_score.items()):
            multiplier[index] = score[1]

        for v in x:
            name = v.name.split(';')
            if '08:30:00' in name[0]:
                lecture_start[0].append(v)
            elif '11:00:00' in name[0]:
                lecture_start[1].append(v)
            elif '13:30:00' in name[0]:
                lecture_start[2].append(v)

        for index,start in enumerate(lecture_start):
            self.model.objective = self.model.objective - multiplier[index]*xsum(start)
        return

    """
    DEPRECATED: THIS WAS A DIFFERENT APPROACH TO THE REPETITIVENESS SCORING WHICH DID NOT PERFORM BETTER
    If two classes are scheduled on the same timeslot in two weeks the ILP has a better score
    This should be more robust to the rational upper bound of the dual and also more robust for occasions such as holidays
    """
    def repetitiveness_two_constecutive_classes(self):
        #Create a sum for every course and a weekly repeating timeslot
        lectures_per_day = 4
        days_per_week = 5
        weeks_per_block = 8
        repetitiveness = [0] * (lectures_per_day*days_per_week*len(self.courses)*(weeks_per_block-1))
        #How many repeating classes shall score
        cost = [self.model.add_var(var_type=INTEGER, name="Cost"+str(i)) for i in range(0,len(repetitiveness))]
        tid = self.get_first_possible_lecture()
        counter = 0
        while tid <= self.free_timeslots[len(self.free_timeslots) - 1]:
            for i in range(0, days_per_week):
                for j in range(0, lectures_per_day):
                    hour = int(8 + 2 * j + (((j + 1) * 30) / 60))
                    tid = tid.replace(hour=hour, minute=((30 + j * 30) % 60))
                    for k, cid in enumerate(self.courses):
                        v = self.model.var_by_name(str(tid) + ';' + cid)
                        tid_plus_one_week = tid + datetime.timedelta(days=7)
                        v_plus_one_week = self.model.var_by_name(str(tid_plus_one_week) + ';' + cid)
                        if v is not None and v_plus_one_week is not None:
                            index = counter*days_per_week*lectures_per_day*len(self.courses) + i*lectures_per_day*len(self.courses)+j*len(self.courses)+k
                            repetitiveness[index] = v + v_plus_one_week
                tid = tid + datetime.timedelta(days=1)
            tid = tid + datetime.timedelta(days=2) #Skip the weekend
            counter += 1
        #If we schedule more than 2,3,4,...,8 classes on the same weekslot, we reward the objective function. This should
        #increase the repetitiveness of the schedule
        for i,r in enumerate(repetitiveness):
            self.model.add_constr(cost[i] == r, name=cost[i].name)

        d = [self.model.add_var(var_type=BINARY,name="D" + str(i)) for i in range(0, len(cost))]

        for i,c in enumerate(cost):
            self.model.add_constr(10*d[i] >= c, name='x'+str(cost[i].name))

        self.model.objective = xsum(d)
        #for d1 in d:
            #self.model.objective = self.model.objective + d1

    """
    If a course is scheduled at least four times on the same day and time we increase the score of the objective function
    """
    def repetitiveness_score(self):
        #Create a sum for every course and a weekly repeating timeslot
        lectures_per_day = 4
        days_per_week = 5
        repetitiveness = [0] * (lectures_per_day*days_per_week*len(self.courses))
        #How many repeating classes shall score
        cost = [self.model.add_var(var_type=INTEGER, name="Cost"+str(i)) for i in range(0,len(repetitiveness))]
        tid = self.get_first_possible_lecture()
        while tid <= self.free_timeslots[len(self.free_timeslots) - 1]:
            for i in range(0, days_per_week):
                for j in range(0, lectures_per_day):
                    hour = int(8 + 2 * j + (((j + 1) * 30) / 60))
                    tid = tid.replace(hour=hour, minute=((30 + j * 30) % 60))
                    for k, cid in enumerate(self.courses):
                        v = self.model.var_by_name(str(tid) + ';' + cid)
                        if v is not None:
                            index = i*len(self.courses)*lectures_per_day+j*len(self.courses)+k
                            repetitiveness[index] = repetitiveness[index] + v
                tid = tid + datetime.timedelta(days=1)
            tid = tid + datetime.timedelta(days=2) #Skip the weekend
        #If we schedule more than 2,3,4,...,8 classes on the same weekslot, we reward the objective function. This should
        #increase the repetitiveness of the schedule
        for i,r in enumerate(repetitiveness):
            self.model.add_constr(cost[i] >= r, name=cost[i].name)

        d = [self.model.add_var(var_type=BINARY,name="D" + str(i)) for i in range(0, len(cost))]

        for i,c in enumerate(cost):
            self.model.add_constr(8*d[i] >= c, name='x'+str(cost[i].name))

        self.model.objective = xsum(d)

    #        for i in range(0,int(len(cost)/len(self.courses))):
#            for j in range(0, len(self.courses)):
#                self.model.add_constr(d[j] <= -cost[i*len(self.courses)+j], name='MaxCost' + str(j) +'xx' + str(i*len(self.courses)+j))

#        for d1 in d:
#            self.model.objective = self.model.objective + d1

    """
    Returns a timeslot which the first Monday, 8:30 of the period
    This is important for the repetitiveness score because the first monday of a period could be a holiday. 
    If this would happen we would score for repetitive schedules on a Saturday. Therefore
    """
    def get_first_possible_lecture(self):
        first_possible_lecture = self.hard_constraints.get_period_info()['StartDate']
        first_possible_lecture = first_possible_lecture.replace(hour=8, minute=30)
        if first_possible_lecture.dayofweek != 0:
            self.logFile.write("WARNING: Period start is not Monday\n")
            diff = datetime.timedelta(first_possible_lecture.dayofweek)
            first_possible_lecture = first_possible_lecture - diff
        return first_possible_lecture
    """
    For every course we sum over all the timeslots in the table and ensure that we schedule exactly as many contact hours 
    as required for that course
    """
    def add_contact_hours_constraint(self):
        #Every course must have exactly #'contact hours' scheduled in the schedule
        for cid,course in self.courses.items():
            self.model.add_constr(xsum(self.model.var_by_name(str(tid)+";"+cid) for tid in self.free_timeslots) == course['Contact hours']/2)#, 'Contact hours '+ cid

    """
    Two courses of the same year should not be taught at the same time
    We add a constraint for every timeslot which sums(timeslot,course) <= 1 for all courses of one year 
    """
    def add_no_course_overlap_constraint(self):
        # We do not want to schedule two courses of the same year in one timeslot

        for tid in self.free_timeslots:
            # We do not want to schedule two courses of the same year in one timeslot
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in self.courses.items() if course['Programme'] == 'BAY1') <= 1)#, 'Overlap BAY1 '+ str(tid)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in self.courses.items() if course['Programme'] == 'BAY2') <= 1)#, 'Overlap BAY2 '+ str(tid)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in self.courses.items() if course['Programme'] == 'BAY3') <= 1)#, 'Overlap BAY3 '+ str(tid)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in self.courses.items() if course['Programme'] == 'MAAIY1') <= 1)#, 'Overlap MAAIY1 ' + str(tid)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in self.courses.items() if course['Programme'] == 'MADSDMY1') <= 1)#, 'Overlap MADSDMY1 ' + str(tid)

    """
    If a teacher teaches more than one course we add a constraint that the sum of the two corresponding courses is <= 1
    for all timeslots
    """
    def add_lecturer_overlap_constraint(self, lecturers):
        lecturer_courses = lecturers.copy()
        # If the teacher just teaches one course we dont have to add a constraint
        for lecturer, course_list in lecturers.items():
            if len(course_list) == 1:
                lecturer_courses.pop(lecturer)

        # For every timeslot add a constraint that at most one of the courses that a teacher teaches is taught
        for tid in self.free_timeslots:
            for lecturer, course_list in lecturer_courses.items():
                self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid in course_list) <= 1)

    """
    If a lecturer is not available at some timeslot we add a constraint = 0 for all courses that he teaches for the
    timeslots that he is not available
    """
    def add_unavailability_constraints(self, lecturers):
        lecturer_unavailability = self.hard_constraints.get_lecturers()
        #If a lecturer is unavailable we do not want to schedule him. Add a = 0  constraint for the timeslots and courses that he teaches
        for lecturer, courses in lecturers.items():
            if lecturer in lecturer_unavailability.keys():
                for cid in courses:
                    for tid in lecturer_unavailability[lecturer]:
                        #constraint_name = ('Unavailable;'+lecturer+';'+str(tid)+';'+cid).replace('-',',').replace(' ','').replace(':',',').replace('ö','oe')
                        #print(constraint_name)
                        self.model.add_constr(self.model.var_by_name(str(tid) + ";" + cid) <= 0)#, name=constraint_name)


    """
    Returns a dictionary in the form <lecturer: [courses taught by lecturer]>
    """
    def get_course_list_of_lecturer(self):
        # Make sure no prof teaches two courses at the same time - Extract the teachers for all courses
        lecturers = {}
        for cid,course in self.courses.items():
            for lecturer in course["Lecturers"].split(';'):
                lecturers.setdefault(lecturer, []).append(cid)
        return lecturers

    """
    Transforms a solution from the ILP to the format that is used to represent our schedules
    """
    def tranform_to_schedule(self):
        courses = self.hard_constraints.get_courses()
        #Iterate over all selected timeslot,course tuples
        for selected_slot in self.selected:
            #Split the tuple into timeslot and course id
            tid,cid = selected_slot.split(";")
            #Extract required information
            prog_id = courses[cid]['Programme']
            room_id = courses[cid]['Lecturers']
            #Fill schedule dictionary with info
            self.schedule.setdefault(tid, []).append({"CourseID": cid, "ProgID": prog_id, "RoomID": room_id})
        #Sort the schedule based on timeslots (hotfix)
        return
#for c in self.model.constrs:
#    print(c)