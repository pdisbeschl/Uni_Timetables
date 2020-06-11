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
from mip import *
from framework.scheduler import Scheduler
"""
A class to build a schedule computed bz an ILP
"""
class ILP(Scheduler):
    def __init__(self):
        super().__init__()
        #Create the ILP model
        self.model = Model()
        #Supresses output from the ILP
        self.model.verbose = 0

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
        free_timeslots = self.hard_constraints.get_free_timeslots()
        courses = self.hard_constraints.get_courses()

        #Define binary decision variables for every course and timeslot. If the variable is 1 it means that the course
        # is scheduled at the timeslot
        x = [self.model.add_var(var_type=BINARY, name=str(tid)+";"+cid)for cid in courses.keys() for tid in free_timeslots]

        #Temporary objective function. It pretty much does nothing useful at the moment. Just adds all courses and timeslots
        #together
        self.model.objective = maximize(xsum(1 * self.model.var_by_name(str(tid)+";"+cid) for cid in courses.keys() for tid in free_timeslots))

        #Every course must have exactly #'contact hours' scheduled in the schedule
        for cid,course in courses.items():
            self.model.add_constr(xsum(self.model.var_by_name(str(tid)+";"+cid) for tid in free_timeslots) == course['Contact hours']/2), 'Contact hours '+ cid

        # We do not want to schedule two courses of the same year in one timeslot
        for tid in free_timeslots:
            # We do not want to schedule two courses of the same year in one timeslot
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in courses.items() if course['Programme'] == 'BAY1') <= 1), 'Overlap BAY1 '+ str(tid)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in courses.items() if course['Programme'] == 'BAY2') <= 1), 'Overlap BAY2 '+ str(tid)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in courses.items() if course['Programme'] == 'BAY3') <= 1), 'Overlap BAY3 '+ str(tid)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in courses.items() if course['Programme'] == 'MAAIY1') <= 1), 'Overlap MAAIY1 ' + str(tid)
            self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid, course in courses.items() if course['Programme'] == 'MADSDMY1') <= 1), 'Overlap MADSDMY1 ' + str(tid)


        #self.model.clear()
        #x = [self.model.add_var(var_type=BINARY, name=str(tid) + ";" + cid) for cid in courses.keys() for tid in free_timeslots]

        #Make sure no prof teaches two courses at the same time - Extract the teachers for all courses
        lecturers = {}
        for cid,course in courses.items():
            for lecturer in course["Lecturers"].split(';'):
                lecturers.setdefault(lecturer, []).append(cid)

        #Create a copy of the courses that a lecturer teaches which is used for unavailability
        lecturer_courses = lecturers.copy()

        # If the teacher just teaches one course we dont have to add a constraint
        for lecturer, course_list in lecturer_courses.items():
            if len(course_list) == 1:
                lecturers.pop(lecturer)

        # For every timeslot add a constraint that at most one of the courses that a teacher teaches is taught
        for tid in free_timeslots:
            for lecturer, course_list in lecturers.items():
                self.model.add_constr(xsum(self.model.var_by_name(str(tid) + ";" + cid) for cid in course_list) <= 1), lecturer

        lecturer_unavailability = self.hard_constraints.get_lecturers()
        for lecturer, courses in lecturer_courses.items():
            if lecturer in lecturer_unavailability.keys():
                for cid in courses:
                    for tid in lecturer_unavailability[lecturer]:
                        self.model.add_constr(self.model.var_by_name(str(tid) + ";" + cid) <= 0)

        ##################################################################################################################
        ##########################NO MORE CONSTRAINTS LOR VARIABLES AFTER THIS############################################
        ##################################################################################################################
        #Solve the ILP
        self.model.optimize(max_seconds=300)

        #Get all timeslot,course tuples which are scheduled
        self.selected = [x[i].name for i in range(len(x)) if x[i].x >= 0.9]
        #Sort the solution by timeslots
        self.selected.sort()



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