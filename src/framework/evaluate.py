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
import datetime


class Evaluate:
    '''This class evaluates a generated timetable.

    The evaluation is performed using some specified metrics.

    The quality indicators "practicals on the same day as lectures" and "stay in the same room vs. change rooms"
    are not taken into account.
    '''

    metrics_file_path = "framework/evaluation_metrics.json"
    score = 0

    def __init__(self, path_to_timetable):
        self.read_metrics()
        self.read_timetable(path_to_timetable)
        # self.check_conflicts() #FIXME not necessary now, also it doesnt check the 'elective' boolean
        self.evaluation()
        print('\n[FINAL RESULT] Schedule score: %0.2f' % (self.score))

    def read_metrics(self):
        print('[INFO] Reading metrics file...')
        with open(os.path.realpath(self.metrics_file_path), "r") as f:
            self.metrics = json.load(f)

        self.preferences = self.metrics['preferences']
        self.weights = self.metrics['weights']

    def read_timetable(self, path):
        print('[INFO] Reading timetable file...')
        with open(os.path.realpath(path), "r") as f:
            self.timetable = json.load(f)

    def check_conflicts(self):
        print('[INFO] Checking conflicts...')
        for day in self.timetable:
            for timeslot in self.timetable[day]:
                prog = []
                room = []
                for c in self.timetable[day][timeslot]:
                    # Programme conclicts (same programme twice in a timeslot)
                    if c['ProgID'] not in prog:
                        prog.append(c['ProgID'])
                    else:
                        raise Exception('Conflict in programme %s on %s at %s' % (c['ProgID'], day, timeslot))
                    # Room conflicts
                    if c['RoomID'] not in room:
                        room.append(c['RoomID'])
                    else:
                        raise Exception('Conflict in room %s on %s at %s' % (c['RoomID'], day, timeslot))
                    # Lecturer conflicts
                    # TODO

        print('[Success] No conflicts.')

    def evaluation(self):
        max_hours = [int(i) for i in self.preferences['max_hours_per_day']]
        starting_times = [i for i in self.preferences['starting_time']]
        max_hours_results = {"fails": [0 for _ in max_hours],
                             "succeeds": [0 for _ in max_hours]}
        starting_times_results = {"fails": [0 for _ in starting_times],
                                  "succeeds": [0 for _ in starting_times]}
        # note: days were there are no lectures at all do not count
        days_off = [i for i in self.preferences['day_off']]
        days_off_results = {"fails": [0 for _ in days_off],
                            "succeeds": [0 for _ in days_off]}
        all_progs = set([c["ProgID"] for timeslot in self.timetable for c in self.timetable[timeslot]])
        break_length = [int(i) for i in self.preferences['break_length']]
        break_length_results = {"fails": [0 for _ in break_length],
                                "succeeds": [0 for _ in break_length]}
        date = ""
        for timeslot in self.timetable:
            if timeslot.split()[0] != date:
                # new day -> new counting everything that is per day
                # first evaluate previous day ...
                if date != "":
                    for prog in hours_per_prog:
                        for i, max in enumerate(max_hours):
                            if hours_per_prog[prog] > max:
                                max_hours_results["fails"][i] += 1
                            else:
                                max_hours_results["succeeds"][i] += 1
                    for prog in starting_time_per_prog:
                        for i, time in enumerate(starting_times):
                            if starting_time_per_prog[prog] != time:
                                starting_times_results["fails"][i] += 1
                            else:
                                starting_times_results["succeeds"][i] += 1
                    for prog in all_progs:
                        if prog in starting_time_per_prog.keys():
                            days_off_results["fails"][day_index] += 1
                        else:
                            days_off_results["succeeds"][day_index] += 1
                    for prog in break_length_per_prog:
                        for i, l in enumerate(break_length):
                            if break_length_per_prog[prog] != l:
                                break_length_results["fails"][i] += 1
                            else:
                                break_length_results["succeeds"][i] += 1
                # ... then reset variables
                date = timeslot.split()[0]
                hours_per_prog = {}
                starting_time_per_prog = {}
                day_index = datetime.datetime.strptime(date, '%Y-%m-%d').weekday()
                break_length_per_prog = {}
            for prog in break_length_per_prog:
                if prog not in [c['ProgID'] for c in self.timetable[timeslot]]:
                    break_length_per_prog[prog] += 1
            # if multiple electives for the same programme are in the same timeslot it should still only count 2 hours
            for prog in set([c['ProgID'] for c in self.timetable[timeslot]]):
                if prog not in hours_per_prog:
                    hours_per_prog.setdefault(prog, 2)
                else:
                    hours_per_prog[prog] += 2  # FIXME I'm assuming every timeslot is 2h long
                # take the earliest course of the programme
                if prog not in starting_time_per_prog:
                    starting_time_per_prog.setdefault(prog, timeslot.split()[1])
                if prog not in break_length_per_prog:
                    break_length_per_prog.setdefault(prog, 0)

        for i, pref in enumerate(self.preferences['max_hours_per_day']):
            print(
                '[RESULT] %i days (separately for each programme) out of %i satisfy the %.2f%% of people who want %s hours/day.' % (
                    max_hours_results["succeeds"][i], max_hours_results["succeeds"][i] + max_hours_results["fails"][i], self.preferences['max_hours_per_day'][pref], pref))
            print('[RESULT] This adds %.2f to the score.' % (max_hours_results["succeeds"][i] * self.preferences['max_hours_per_day'][pref]))
            self.score += (max_hours_results["succeeds"][i] * self.preferences['max_hours_per_day'][pref]) * self.weights['max_hours_per_day']
        for i, pref in enumerate(self.preferences['starting_time']):
            print(
                '[RESULT] %i days (separately for each programme) out of %i satisfy the %.2f%% of people who want to start at %s.' % (
                    starting_times_results["succeeds"][i], starting_times_results["succeeds"][i] + starting_times_results["fails"][i],
                    self.preferences['starting_time'][pref], pref))
            print('[RESULT] This adds %.2f to the score.' % (
                        starting_times_results["succeeds"][i] * self.preferences['starting_time'][pref]))
            self.score += (starting_times_results["succeeds"][i] * self.preferences['starting_time'][pref]) * self.weights['starting_time']
        for i, pref in enumerate(self.preferences['day_off']):
            print(
                '[RESULT] %i days (separately for each programme) out of %i satisfy the %.2f%% of people who want a day off on %s.' % (
                    days_off_results["succeeds"][i], days_off_results["succeeds"][i] + days_off_results["fails"][i],
                    self.preferences['day_off'][pref], pref))
            print('[RESULT] This adds %.2f to the score.' % (
                        days_off_results["succeeds"][i] * self.preferences['day_off'][pref]))
            self.score += (days_off_results["succeeds"][i] * self.preferences['day_off'][pref]) * self.weights['day_off']
        for i, pref in enumerate(self.preferences['break_length']):
            print(
                '[RESULT] %i days (separately for each programme) out of %i satisfy the %.2f%% of people who want a break of %s timeslots.' % (
                    break_length_results["succeeds"][i], break_length_results["succeeds"][i] + break_length_results["fails"][i],
                    self.preferences['break_length'][pref], pref))
            print('[RESULT] This adds %.2f to the score.' % (
                        break_length_results["succeeds"][i] * self.preferences['break_length'][pref]))
            self.score += (break_length_results["succeeds"][i] * self.preferences['break_length'][pref]) * self.weights['break_length']


if __name__ == "__main__":
    e = Evaluate('../InputOutput/out.json')
