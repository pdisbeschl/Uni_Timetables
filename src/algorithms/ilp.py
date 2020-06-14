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
        #Get the evaluation metrics
        metrics_file_path = "framework/evaluation_metrics.json"
        with open(os.path.realpath(metrics_file_path), "r") as f:
            self.metrics = json.load(f)

        #This could or should be less static
        self.lectures_per_day = 4
        self.days_per_week = 5
        self.weeks_per_block = 8


        #Create the ILP model
        self.model = Model(sense=MINIMIZE, solver_name=CBC)
        #Enable/Supresses output from the ILP
        self.model.verbose = 0
        #Allow all cores to be used for faster runtime
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

        #Add all soft constraints which have an effect on the objective function
        #Add a score to the objective function based on how repetitive the schedule is
        self.repetitiveness_score()
        #Add a score to the objective function based on when the first lecture of the day starts
        self.lecture_start_score(x, 1)
        #Add a score to the objective function based on how many lectures are scheduled per day
        self.classes_per_day_score(1)

        #Add all hard constraints to the ILP - they have no effect on the objective function
        #Ensure that every course is taught exactly the required hours
        self.add_contact_hours_constraint()
        #Ensure that two courses of the same year do not fall on the same timeslot
        self.add_no_course_overlap_constraint()
        #Ensure that noone has to teach two courses at the same time
        self.add_lecturer_overlap_constraint(lecturers)
        #Ensure that noone has to teach when he is not available
        self.add_unavailability_constraints(lecturers)


        #Uncomment to write the ILP as a text file
        #self.model.write('model.lp')

        ##################################################################################################################
        ##########################NO MORE CONSTRAINTS OR VARIABLES AFTER THIS#############################################
        ##################################################################################################################
        #Solve the ILP (optinally configure some more parameters)
        #self.model.seed = int(time.time())
        #self.model.max_mip_gap = 5
        #self.model.integer_tol = 0.25
        #self.model.max_mip_gap_abs = 5
        #Allow a maximum of 20 seconds to find a feasible solution and improve on it
        status = self.model.optimize(max_seconds=20)
        #Get all timeslot,course tuples which are scheduled
        self.selected = [x[i].name for i in range(len(x)) if x[i].x >= 0.9]
        #Sort the solution by timeslots
        self.selected.sort()


    """
    For every year we want to find the number of classes which are scheduled on a timeslot. For every timeslot the number 
    of scheduled classes is scored based on the score obtained by the survey
    """
    def classes_per_day_score(self, importance):
        #Create a dictionary of all the years that are currently taught. Should be made dynamic
        index_dict = {'BAY1': 0,'BAY2': 1,'BAY3': 2,'MAAIY1': 3,'MADSDMY1': 4}
        #Create a list for the sum for every course for every day where classes can occur0
        lectures_per_day_sum = [0] * (self.weeks_per_block*self.days_per_week)
        #Get the period start and initialise a counter in which week we currently are
        tid = self.get_first_possible_lecture()
        week_counter = 0
        #Iterate over all days of the period
        while tid <= self.free_timeslots[len(self.free_timeslots) - 1]:
            for i in range(0, self.days_per_week):
                #For every year create a list which holds a linear expression of the decision variables for scheduled lectures
                lectures_scheduled_per_day = [0] * 5
                #Iterate over all courses
                for k, cid in enumerate(self.courses):
                    #Find the index for the lectures_scheduled_per_day to which we want to add the sum of the classes on the day
                    index = index_dict[self.courses[cid]['Programme']]
                    #Iterate over all timeslots for this day. Semi hard coded
                    for j in range(0, self.lectures_per_day):
                        hour = int(8 + 2 * j + (((j + 1) * 30) / 60))
                        tid = tid.replace(hour=hour, minute=((30 + j * 30) % 60))
                        #Get the decision variable for the current (timeslot,course) and if exists add the sum of lecturs on the day to the corresponding year
                        v = self.model.var_by_name(str(tid) + ';' + cid)
                        if v is not None:
                            lectures_scheduled_per_day[index] = lectures_scheduled_per_day[index] + v
                tid = tid + datetime.timedelta(days=1)
                lectures_per_day_sum[week_counter * self.days_per_week+i] = lectures_scheduled_per_day
            tid = tid + datetime.timedelta(days=2) #Skip the weekend
            week_counter += 1

        #Create binary variables which indicate if we schedule less than 2,4,6 or 8 hours a day. These are added to the objective function with given weights
        lectures_per_day_2 = [self.model.add_var(var_type=BINARY,name="HoursPerDay2x" + str(i)) for i in range(0, len(lectures_per_day_sum)*len(index_dict))]
        lectures_per_day_4 = [self.model.add_var(var_type=BINARY,name="HoursPerDay4x" + str(i)) for i in range(0, len(lectures_per_day_sum)*len(index_dict))]
        lectures_per_day_6 = [self.model.add_var(var_type=BINARY,name="HoursPerDay6x" + str(i)) for i in range(0, len(lectures_per_day_sum)*len(index_dict))]
        lectures_per_day_8 = [self.model.add_var(var_type=BINARY,name="HoursPerDay8x" + str(i)) for i in range(0, len(lectures_per_day_sum)*len(index_dict))]

        #Create constraints for all the days and years that we have in the form of BigM*d<=lectures on day. If d=1 it is good
        #for the objective function and this we want as many variables to be 1 as possible. Note that if we schedule less than four hours
        #we also schedule less than 6 and 8. Therefore, the fewer hours a day, the better.
        for j,lectures_per_day_for_year in enumerate(lectures_per_day_sum):
            for i,lectures_on_day in enumerate(lectures_per_day_for_year):
                self.model.add_constr(1*lectures_per_day_2[j*len(lectures_per_day_for_year)+i] <= lectures_on_day, name='y'+str(j)+str(lectures_per_day_2[j*len(lectures_per_day_for_year)+i].name))
                self.model.add_constr(2*lectures_per_day_4[j*len(lectures_per_day_for_year)+i] <= lectures_on_day, name='y'+str(j)+str(lectures_per_day_4[j*len(lectures_per_day_for_year)+i].name))
                self.model.add_constr(3*lectures_per_day_6[j*len(lectures_per_day_for_year)+i] <= lectures_on_day, name='y'+str(j)+str(lectures_per_day_6[j*len(lectures_per_day_for_year)+i].name))
                self.model.add_constr(4*lectures_per_day_8[j*len(lectures_per_day_for_year)+i] <= lectures_on_day, name='y'+str(j)+str(lectures_per_day_8[j*len(lectures_per_day_for_year)+i].name))

        #Extract the score for the number of maximal hours scheduled per day.
        #This should be more generic
        hour_score = self.metrics['preferences']['max_hours_per_day']
        factor_two = sum(hour_score.values())*importance#*0 Uncommenting this results in basically no 2 hour lectures
        factor_four = sum(hour_score.values())*importance
        factor_six = hour_score['6'] + hour_score['8']*importance
        factor_eight = hour_score['8']*importance

        #Add the binary variables to the objective function with respective weights
        self.model.objective = self.model.objective - xsum(lectures_per_day_2)*factor_two
        self.model.objective = self.model.objective - xsum(lectures_per_day_4)*factor_four
        self.model.objective = self.model.objective - xsum(lectures_per_day_6)*factor_six
        self.model.objective = self.model.objective - xsum(lectures_per_day_8)*factor_eight


    """
    We add a score for the start time of each lecture. If we can place a lecture at 11:00 it is better than placing it
    at 16:00
    NOTE: This currently has the effect that the first lecture will be scheduled at 11:00, the second lecture at 8:30
    and the third lecture at 13:30. The last lecture consequently at 16:00. 
    It does not consider at what thime the first lecture is scheduled but only prioritises scheduling slots
    """
    def lecture_start_score(self, x, importance):
        lecture_start = [[],[],[]]
        #Load the metrics from the survey and extract the score for each respective multipliers
        start_score = self.metrics['preferences']['starting_time']
        multiplier = [0] * len(start_score)
        for index, score in enumerate(start_score.items()):
            multiplier[index] = score[1]

        #Iterate over all timeslot;course decision variables and add them to an array based on their starting time
        # This is very hard coded. Based on the survey we only have scores for three starting times
        for v in x:
            name = v.name.split(';')
            if '08:30:00' in name[0]:
                lecture_start[0].append(v)
            elif '11:00:00' in name[0]:
                lecture_start[1].append(v)
            elif '13:30:00' in name[0]:
                lecture_start[2].append(v)

        #For every starting timeslot we add a score based on the values obtained in the survey
        #If a class is not scheduled the decision variable is 0 and thus has no effect
        for index,start in enumerate(lecture_start):
            self.model.objective = self.model.objective - multiplier[index]*xsum(start) * importance
        return


    """
    We want our schedule to show some kind of repetitive pattern
    For every repeating timeslot we count the number of scheduled classes (i.e. Monday 8:30). We then create a integer 
    variable 'cost' which represents the aforementioned sum of classes on a timeslot. As a last step we create a binary 
    decision variable 'd' which is multiplied with a BigM (here 10 is chosen because we have at most 8 weeks) and add
    a constraint such that "BigM * d >= cost". 
    This constraint causes the binary variable to be 1 if there is at least one class scheduled for a repeating timeslot.
    We add all decision variables d to the objective function and since we want to minimize we want as little d variables
    to be 1 as possible.
    This is archived by scheduling classes in a repeating fashion. Why? Constraint (1) 10*d1>=2 means that there are two
    classes scheduled on a given repeating timeslot. If we were to split these two classes on two different timeslots we
    would have two constraints of the form (2) 10*d1>=1 and 10*d2>=1. If we have case (2) we add a value of 2 to the obj.
    function whereas (1) only adds 1 the the obj. function     
    """
    def repetitiveness_score(self):
        #Create a sum for every course and a weekly repeating timeslot. This holds the linear expression of all rep. timeslots
        repetitiveness = [0] * (self.lectures_per_day*self.days_per_week*len(self.courses))
        #Create an integer variable which is the sum of linear expression for the repeating classes on a timeslot
        cost = [self.model.add_var(var_type=INTEGER, name="Cost"+str(i)) for i in range(0,len(repetitiveness))]

        #Iterate over all timeslots from the start of the period to the end. Alternatively we could iterate over timeslots with a pattern
        tid = self.get_first_possible_lecture()
        while tid <= self.free_timeslots[len(self.free_timeslots) - 1]:
            #Iterate over the five day of a week
            for i in range(0, self.days_per_week):
                #Every day of the week we have a numver of lectures
                for j in range(0, self.lectures_per_day):
                    #Calculate the number of lectures. Semi hard coded - 8=start first lecture; 2=lecture duration; 30=break length
                    hour = int(8 + 2 * j + (((j + 1) * 30) / 60))
                    tid = tid.replace(hour=hour, minute=((30 + j * 30) % 60))
                    #Iterate over all courses for the current timeslot
                    for k, cid in enumerate(self.courses):
                        #Find the decision variable of that timeslot;course combo and if it exists...
                        v = self.model.var_by_name(str(tid) + ';' + cid)
                        if v is not None:
                            #add it to the linear expression counting the number of repeated lectures on a timeslot
                            index = i*len(self.courses)*self.lectures_per_day+j*len(self.courses)+k
                            repetitiveness[index] = repetitiveness[index] + v
                tid = tid + datetime.timedelta(days=1)
            tid = tid + datetime.timedelta(days=2) #Skip the weekend
        #Assign the integer variable cost to the number scheduled lectures. The >= constraint will be tight but allows for robustness
        for i,r in enumerate(repetitiveness):
            self.model.add_constr(cost[i] >= r, name=cost[i].name)

        #Create a decision variable create a constraint in the form BigM*d[i]>=cost[i] for all i.
        d = [self.model.add_var(var_type=BINARY,name="D" + str(i)) for i in range(0, len(cost))]
        for i,c in enumerate(cost):
            self.model.add_constr(10*d[i] >= c, name='x'+str(cost[i].name))

        #Add all binary decision variables to the objective function
        self.model.objective = xsum(d)

    """
    Returns a timeslot which the first Monday, 8:30 of the period
    This is important for the repetitiveness score because the first monday of a period could be a holiday. 
    If this would happen we would score for repetitive schedules on a Saturday.
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
    as required for that course. The constraint is sum(decision variables course)=contact hours course for every course
    """
    def add_contact_hours_constraint(self):
        #Every course must have exactly #'contact hours' scheduled in the schedule
        for cid,course in self.courses.items():
            self.model.add_constr(xsum(self.model.var_by_name(str(tid)+";"+cid) for tid in self.free_timeslots) == course['Contact hours']/2)#, 'Contact hours '+ cid

    """
    Two courses of the same year should not be taught at the same time
    We add a constraint for every timeslot which sums(timeslot,course) <= 1 for all courses of one year 
    The constraint is for every timeslot we create a constraint for every year in the form of 
    sum(courses of the year at timeslot) <= 1 for every year for every timeslot
    """
    def add_no_course_overlap_constraint(self):
        # We do not want to schedule two courses of the same year in one timeslot. Iterate over all timeslots
        for tid in self.free_timeslots:
            # For every timeslot make sure that the sum of scheduled lectures is at most 1, i.e. we schedule no more than one couse in each timeslot
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in self.courses.items() if course['Programme'] == 'BAY1') <= 1)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in self.courses.items() if course['Programme'] == 'BAY2') <= 1)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in self.courses.items() if course['Programme'] == 'BAY3') <= 1)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in self.courses.items() if course['Programme'] == 'MAAIY1') <= 1)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in self.courses.items() if course['Programme'] == 'MADSDMY1') <= 1)

    """
    No teacher can have two lectures at the same time. For every timeslot we create a constraint that the number of courses
    that he teaches at that timeslot is at most 1
    """
    def add_lecturer_overlap_constraint(self, lecturers):
        #Get dictionary of all lecturers with a list of courses that he teaches {'lecturer':[courses]}
        lecturer_courses = lecturers.copy()
        #If the teacher just teaches one course the constraint is satisfied by default. No need to add it
        for lecturer, course_list in lecturers.items():
            if len(course_list) == 1:
                lecturer_courses.pop(lecturer)

        #For every timeslot add a constraint that at most one of the courses that a teacher teaches is taught
        for tid in self.free_timeslots:
            for lecturer, course_list in lecturer_courses.items():
                self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid in course_list) <= 1)

    """
    If a lecturer is not available at some timeslot we add a constraint = 0 for all courses that he teaches for the
    timeslots that he is not available
    """
    def add_unavailability_constraints(self, lecturers):
        #Get the timeslots where a teacher is unavailable
        lecturer_unavailability = self.hard_constraints.get_lecturers()
        #If a lecturer is unavailable we do not want to schedule him. Add a = 0  constraint for the timeslots and courses that he teaches
        #Iterate over all lecturers and the courses that he teaches
        for lecturer, courses in lecturers.items():
            #Iterate over all teachers that have unavailable timeslot
            if lecturer in lecturer_unavailability.keys():
                #Iterate over the courses that the teacher teaches
                for cid in courses:
                    #Iterate over the unavailable timeslots of the current teacher
                    for tid in lecturer_unavailability[lecturer]:
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
    The decision variables for a (timeslot,course) tuple are 1 if a course is scheduled and 0 if not
    """
    def tranform_to_schedule(self):
        courses = self.hard_constraints.get_courses()
        #Iterate over all selected timeslot,course tuples
        for selected_slot in self.selected:
            #Split the tuple into timeslot and course id
            tid,cid = selected_slot.split(";")
            #Extract required information
            prog_id = courses[cid]['Programme']
            lecturers = courses[cid]['Lecturers']
            name = courses[cid]['Course name']
            #Fill schedule dictionary with info
            self.schedule.setdefault(tid, []).append({"CourseID": cid, "Name": name, "ProgID": prog_id, "RoomID": "-1", "Lecturers": lecturers})
        return
