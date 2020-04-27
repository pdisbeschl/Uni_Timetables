"""
Evaluate the generated timetables according to the given metrics
===================

author: Huy Ngo
author: Yu Fee Chan
author: Daniel Kaestner
author: Paul Disbeschl
author: Guillermo Quintana Pelayo
author: Camilla Lummerzheim

Documented following PEP 257.
"""
import sys
import json
import os

class Evaluate:
    '''This class evaluates a generated timetable.

    The evaluation is performed using some specified metrics.
    '''

    metrics_file_path = "./evaluation_metrics.json"
    score = 0

    def __init__(self, path_to_timetable):
        self.read_metrics()
        self.read_timetable(path_to_timetable)
        self.check_conflicts()
        self.greedy_evaluation()
        print(self.score)

    def read_metrics(self):
        print('[Info] Reading metrics file...')
        with open(os.path.realpath(self.metrics_file_path),"r") as f:
            self.metrics = json.load(f)
        
        self.preferences = self.metrics['preferences']
        #print(self.preferences)
    
    def read_timetable(self, path):
        print('[Info] Reading timetable file...')
        with open(os.path.realpath(path),"r") as f:
            self.timetable = json.load(f)
            
    def check_conflicts(self):
        print('[info] Checking conflicts...')
        for day in self.timetable:
            for timeslot in self.timetable[day]:
                prog = []
                room = []
                for c in self.timetable[day][timeslot]:
                    #Programme conclicts (same programme twice in a timeslot)
                    if c['ProgID'] not in prog:
                        prog.append(c['ProgID'])
                    else:
                        raise Exception('Conflict in programme %s on %s at %s'%(c['ProgID'],day,timeslot))
                    #Room conflicts
                    if c['RoomID'] not in room:
                        room.append(c['RoomID'])
                    else:
                        raise Exception('Conflict in room %s on %s at %s'%(c['RoomID'],day,timeslot))
                    #Lecturer conflicts
                    #TODO

        print('[Success] No conflicts.')

    def greedy_evaluation(self):
        #metrics_names = ['max_hours_per_day','starting_time','break_length','same_schedule_every_week','day_off']
        for m in self.preferences:
            print('[info] Resolving metric: %s'%(m))
            if m == 'max_hours_per_day':
                #Check for each day if the max hours is reached
                fails = 0
                max = self.preferences[m]
                for day in self.timetable:
                    hours_per_prog = {}
                    for timeslot in self.timetable[day]:
                        for c in self.timetable[day][timeslot]:
                            if c['ProgID'] not in hours_per_prog:
                                hours_per_prog.setdefault(c['ProgID'], 2)
                            else:
                                hours_per_prog[c['ProgID']] += 2 #FIXME I'm assuming every timeslot is 2h long
                    for i in hours_per_prog:
                        if hours_per_prog[i] >max:
                            fails+=1
                            break #If this break is removed then it count the total fails
                days_count = len(self.timetable.keys())
                print('[Result] %i days out of %i meet the requirement.'%(days_count - fails, days_count))
                self.score -= fails


if __name__ == "__main__":
    e = Evaluate('../InputOutput/out.json')