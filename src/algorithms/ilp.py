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
            self.model.add_constr(xsum(self.model.var_by_name(str(tid)+";"+cid) for tid in free_timeslots) == course['Contact hours']/2)

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
            #Fill schedule dictionary with info
            self.schedule.setdefault(tid, []).append({"CourseID": cid, "ProgID": prog_id, "RoomID": "-1"})
        #Sort the schedule based on timeslots (hotfix)
        return
