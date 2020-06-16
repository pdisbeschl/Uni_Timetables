"""
Genetic Timetable scheduler
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
import numpy as np
import random
import math
from datetime import timedelta
import datetime

"""
idea:
1. initialization population (instance timetable), each gene contains room information(capacity,room id) and course information(subject, num of students, teachers)
2. calculate fitness function for each individual from population based on constraints.
3. select pair of parents to crossover new child.
4. the new child is then undergone throung mution.
5. iteration the loop until find feasible timetable.

"""


class Genetic(Scheduler):
    def __init__(self, excel_file_path='./InputOutput/Sample.xlsx'):
        super().__init__(excel_file_path)
        self.population = []
        self.population_size = 10
        self.individual_size = 20 * 8
        self.generations = 2000
        self.crossover_probability = 0.8
        self.mutation_probability = 0.01
        self.rooms = self.hard_constraints.get_rooms()
        self.default_courses = self.hard_constraints.get_courses()
        self.timeslots = self.hard_constraints.get_free_timeslots()
        self.holidays = self.hard_constraints.get_holidays()
        self.courses = self.divide_courses_to_slot()

    def generate_timetable(self):
        print("Running genetic...")
        self.generations = len(self.courses) * 100
        self.create_population()
        pop = self.population
        final_idx = 0
        count = 1
        check_soft_constraints = True

        # num of constraints * courses
        if check_soft_constraints:
            max_fit = 6 * len(self.courses) + 1
            self.generations += 1000
        else:
            max_fit = 5 * len(self.courses)

        flag_reduce = True

        # stop when satisfying all hard constraints or reach generation th
        while self.fitness(pop[final_idx]) < max_fit and count < self.generations:
            list_fitness_pop = []
            for i in pop:
                score = self.fitness(i, check_soft_constraints)
                list_fitness_pop.append(score)

            parent1, parent2 = self.selection()
            # parent1, parent2 = self.selection1(list_fitness_pop)
            individual1_new, individual2_new = self.crossover(parent1, parent2)
            individual1_new = self.mutation(individual1_new)
            individual2_new = self.mutation(individual2_new)

            # check if new generations are better or not.
            # If yes replace weakest individuals from previous generation with new generations
            if self.fitness(individual1_new) > self.fitness(pop[np.argmin(list_fitness_pop)]):
                pop[np.argmin(list_fitness_pop)] = individual1_new
                list_fitness_pop[np.argmin(list_fitness_pop)] = self.fitness(individual1_new)
            if self.fitness(individual2_new) > self.fitness(pop[np.argmin(list_fitness_pop)]):
                pop[np.argmin(list_fitness_pop)] = individual2_new
                list_fitness_pop[np.argmin(list_fitness_pop)] = self.fitness(individual2_new)

            final_idx = np.argmax(list_fitness_pop)

            count += 1
            if self.fitness(pop[final_idx]) >= 5 * len(self.courses):
                print("gen {}/{} best fit: {}/{} rate {:.2f}% (maybe satisfy all hard constraints)".format(
                    count, self.generations, self.fitness(pop[final_idx]), max_fit,
                    self.fitness(pop[final_idx]) / max_fit * 100))
            else:
                print("gen {}/{} best fit: {}/{} rate {:.2f}%".format(
                    count, self.generations, self.fitness(pop[final_idx]), max_fit,
                    self.fitness(pop[final_idx]) / max_fit * 100))

            if flag_reduce and self.fitness(pop[final_idx]) == 5 * len(self.courses):
                self.generations = count + 1000
                print("maybe get feasible schedule, reduce runtime!")
                flag_reduce = False

        print("done!")
        print("fail {}".format(max_fit - self.fitness(pop[final_idx])))
        result = pop[final_idx]
        result = self.fill_timeslot(result)
        result = self.convert_to_schedule(result)
        self.copy_schedule(result, distribution_timeslot=True)

    def crossover(self, individual1, individual2):
        individual1_new = individual1.copy()
        individual2_new = individual2.copy()

        for i in range(self.individual_size):
            if random.random() < self.crossover_probability:
                # find course id to crossover
                ind1_course_id = individual1_new[i]
                ind2_course_id = individual2_new[i]

                ind1_idx = np.where(individual1_new == ind2_course_id)[0][0]
                ind2_idx = np.where(individual2_new == ind1_course_id)[0][0]

                individual1_new[i] = ind2_course_id
                individual2_new[i] = ind1_course_id

                individual1_new[ind1_idx] = ind1_course_id
                individual2_new[ind2_idx] = ind2_course_id
        return individual1_new, individual2_new

    def mutation(self, individual):
        individual_m = individual.copy()
        for i in range(self.individual_size):
            if random.random() < self.mutation_probability:
                while True:
                    selected_idx = random.randint(0, self.individual_size - 1)
                    if selected_idx != i:
                        break
                m_id = individual_m[i]
                individual_m[i] = individual_m[selected_idx]
                individual_m[selected_idx] = m_id
        return individual_m

    # tournament selection
    def selection(self, tournament_size=4):
        population = self.population
        pop_size = self.population_size
        parents = []
        indices = list(range(pop_size))
        random.shuffle(indices)
        for i in range(tournament_size):
            parents.append(population[indices[i]])

        # find parent1
        if self.fitness(parents[0]) > self.fitness(parents[1]):
            parent1 = parents[0]
        else:
            parent1 = parents[1]
        # find parent2
        if self.fitness(parents[2]) > self.fitness(parents[3]):
            parent2 = parents[2]
        else:
            parent2 = parents[3]

        return parent1, parent2

    # TODO: test only remove when done
    # best fitness selection
    def selection1(self, list_fitness_pop):
        population = self.population
        l = np.array(list_fitness_pop)
        par1_idx, par2_idx = l.argsort()[-2:][::-1]
        parent1 = population[par1_idx]
        parent2 = population[par2_idx]
        return parent1, parent2

    def fitness(self, individual, check_soft_constraints=False):
        courses = self.courses
        rooms = self.rooms
        list_courses = list(courses)
        lis_rooms = list(rooms)
        score = 0
        day_off_score = {}

        for count, g in enumerate(individual):
            if g != 0:
                c = courses[list_courses[int(g) - 1]]
                r = rooms[lis_rooms[count % 8]]
                s = math.floor(count / 8)
                # room capacity constraint
                if c["Number of students"] <= r["Capacity"]:
                    score += 1
                # lecturers constraint
                if not self.has_lecturer_conflict(g, count, individual):
                    score += 1
                # slot constraint
                if not self.has_slot_conflict(g, count):
                    score += 1
                # room constraint
                if not self.has_room_conflict(g, count, individual):
                    score += 1
                if not self.has_programme_conflict(g, count, individual):
                    score += 1
                # use to satisfy soft constraints
                if check_soft_constraints:
                    # start at 11pm
                    if s == 2:
                        score += 1
                    # Friday FREEDOM !!!
                    if count < 32:
                        if "Mon" not in day_off_score.keys():
                            day_off_score["Mon"] = 1
                        else:
                            day_off_score["Mon"] += 1
                    elif 32 <= count < 64:
                        if "Tue" not in day_off_score.keys():
                            day_off_score["Tue"] = 1
                        else:
                            day_off_score["Tue"] += 1
                    elif 64 <= count < 96:
                        if "Wed" not in day_off_score.keys():
                            day_off_score["Wed"] = 1
                        else:
                            day_off_score["Wed"] += 1
                    elif 96 <= count < 128:
                        if "Thu" not in day_off_score.keys():
                            day_off_score["Thu"] = 1
                        else:
                            day_off_score["Thu"] += 1
                    else:
                        if "Fri" not in day_off_score.keys():
                            day_off_score["Fri"] = 1
                        else:
                            day_off_score["Fri"] += 1

        if check_soft_constraints and min(day_off_score, key=day_off_score.get) == "Fri":
            score += 1
        return score

    # individual is list of classes (course with timeslot and room)
    def create_population(self):
        courses = list(range(1, len(self.courses) + 1))
        for p in range(self.population_size):
            # 20 slots, 8 rooms per week
            individual = np.zeros(20 * 8)
            c = 0
            while c < len(courses):
                pos = random.randint(0, 20 * 8 - 1)
                if individual[pos] == 0:
                    individual[pos] = courses[c]
                    c += 1
            self.population.append(individual)

    def get_schedule(self):
        return self.schedule

    def convert_to_schedule(self, schedule):
        schedule_result = {}
        list_courses = list(self.courses)
        list_rooms = list(self.rooms)
        c_room = 0
        count = 0
        schedule = schedule.reshape(20, 8)
        for data in schedule:
            for i in data:
                if i != 0:
                    course_id = list_courses[int(i) - 1]
                    course_id = course_id.split("_")[0]
                    course = self.default_courses[course_id]
                    prog_id = course["Programme"]
                    room_id = list_rooms[c_room]
                    lecturers = course['Lecturers']
                    name = course['Course name']
                    self.schedule.setdefault(str(self.timeslots[count]), []).append(
                        {"CourseID": course_id, "Name": name, "ProgID": prog_id, "RoomID": room_id,
                         "Lecturers": lecturers})
                    schedule_result.setdefault(self.timeslots[count], []).append(
                        {"CourseID": course_id, "Name": name, "ProgID": prog_id, "RoomID": room_id,
                         "Lecturers": lecturers})
                    course['Contact hours'] -= 2
                c_room += 1
            count += 1
            c_room = 0
        return schedule_result

    def copy_schedule(self, schedule, distribution_timeslot=False):
        holidays = self.holidays
        period_end = self.hard_constraints.period_info["EndDate"]
        week_counter = 1
        first_lecture = next(iter(schedule.keys()))
        courses = self.default_courses
        while first_lecture + timedelta(days=7 * week_counter) < period_end:
            list_slots_per_week = {}
            for date, scheduled_courses in schedule.items():
                date = date + timedelta(days=7 * week_counter)
                dt = str(date).split()[0]
                dt = datetime.datetime.strptime(dt, '%Y-%m-%d')
                if holidays[dt] == 0:
                    for course in scheduled_courses:
                        course_id = course["CourseID"]
                        prog_id = course["ProgID"]
                        room_id = course["RoomID"]
                        lecturers = course['Lecturers']
                        name = course['Name']

                        if distribution_timeslot:
                            contact_hours = int(courses[course_id]["Contact hours"] / 2)
                            needed_slot_per_week = math.ceil(contact_hours / 7)
                            if course_id not in list_slots_per_week.keys():
                                list_slots_per_week[course_id] = needed_slot_per_week
                                if week_counter >= 4:
                                    list_slots_per_week[course_id] = 3

                        if courses[course_id]['Contact hours'] > 0:
                            if distribution_timeslot:
                                if list_slots_per_week[course_id] > 0:
                                    list_slots_per_week[course_id] -= 1
                                    self.schedule.setdefault(str(date), []).append(
                                        {"CourseID": course_id, "Name": name, "ProgID": prog_id, "RoomID": room_id,
                                         "Lecturers": lecturers})
                                    courses[course_id]['Contact hours'] -= 2
                            else:
                                self.schedule.setdefault(str(date), []).append(
                                    {"CourseID": course_id, "Name": name, "ProgID": prog_id, "RoomID": room_id,
                                     "Lecturers": lecturers})
                                courses[course_id]['Contact hours'] -= 2
            week_counter += 1

    # check lecture conflict in slot time of day
    # gen = class
    def has_lecturer_conflict(self, gen, pos, individual):
        courses = self.courses
        list_courses = list(courses)
        # low,high = row
        low_slot = pos - (pos % 8)
        high_slot = (math.floor(low_slot / 32) + 1) * 32

        gen_course_id = list_courses[int(gen) - 1]
        gen_course = courses[gen_course_id]
        lecturers = gen_course["Lecturers"].split(';')
        needed_slot_per_week = self.calculate_need_slot_per_week(gen_course_id)

        check_slot = low_slot + (needed_slot_per_week * 8)
        if check_slot < high_slot:
            high_slot = check_slot
        for g in individual[low_slot:high_slot]:
            if g != 0 and g != gen:
                c = courses[list_courses[int(g) - 1]]
                list_lecturers = c["Lecturers"].split(';')
                for l in list_lecturers:
                    if l in lecturers:
                        return True
        return False

    def has_slot_conflict(self, gen, pos):
        courses = self.courses
        list_courses = list(courses)
        # start, end = column
        # 32 slots per day
        start_slot = (pos % 8) + math.floor(pos / 32) * 32
        end_slot = start_slot + 24

        gen_course_id = list_courses[int(gen) - 1]
        needed_slot_per_week = self.calculate_need_slot_per_week(gen_course_id)
        if (pos + 8 * (needed_slot_per_week - 1)) > end_slot:
            return True
        return False

    # check room conflict in same day
    def has_room_conflict(self, gen, pos, individual):
        courses = self.courses
        list_courses = list(courses)
        # start, end = column
        # 32 slots per day
        start_slot = (pos % 8) + math.floor(pos / 32) * 32
        end_slot = start_slot + 24

        gen_course_id = list_courses[int(gen) - 1]
        needed_slot_per_week = self.calculate_need_slot_per_week(gen_course_id)
        for i in range(pos + 8, end_slot + 1, 8):
            needed_slot_per_week -= 1
            if individual[i] != 0 and needed_slot_per_week != 0:
                return True
        return False

    def has_programme_conflict(self, gen, pos, individual):
        courses = self.courses
        list_courses = list(courses)
        # low,high = row
        low_slot = pos - (pos % 8)
        high_slot = (math.floor(low_slot / 32) + 1) * 32

        gen_course_id = list_courses[int(gen) - 1]
        gen_course = courses[gen_course_id]
        programme = gen_course["Programme"]
        needed_slot_per_week = self.calculate_need_slot_per_week(gen_course_id)

        check_slot = low_slot + (needed_slot_per_week * 8)
        if check_slot < high_slot:
            high_slot = check_slot
        for g in individual[low_slot:high_slot]:
            if g != 0 and g != gen:
                c = courses[list_courses[int(g) - 1]]
                if programme == c["Programme"]:
                    return True
        return False

    def fill_timeslot(self, data):
        courses = self.courses
        list_courses = list(courses)
        new_timetable = data.copy()
        for idx, value in enumerate(data):
            if value != 0:
                start_slot = (idx % 8) + math.floor(idx / 32) * 32
                end_slot = start_slot + 24
                gen_course_id = list_courses[int(value) - 1]
                needed_slot_per_week = self.calculate_need_slot_per_week(gen_course_id)
                needed_slot_per_week -= 1
                for i in range(idx + 8, end_slot + 1, 8):
                    if new_timetable[i] == 0:
                        if needed_slot_per_week > 0:
                            new_timetable[i] = value
                            needed_slot_per_week -= 1
                    else:
                        break
        return new_timetable

    def calculate_need_slot_per_week(self, course_id):
        contact_hours = int(self.courses[course_id]["Contact hours"] / 2)
        needed_slot_per_week = math.ceil(contact_hours / 7)
        return needed_slot_per_week

    def divide_courses_to_slot(self):
        list_courses_by_slot = {}
        list_courses_per_programme = {}
        for k, v in self.default_courses.items():
            programme_name = v["Programme"]
            list_courses_per_programme.setdefault(programme_name, []).append(k)

        for k, v in list_courses_per_programme.items():
            if len(v) > 5:
                for c in v:
                    contact_hours = int(self.default_courses[c]["Contact hours"] / 2)
                    needed_slot_per_week = math.ceil(contact_hours / 7)
                    course = self.default_courses[c].copy()
                    course1 = self.default_courses[c].copy()
                    full_contact_hours = course["Contact hours"]
                    if needed_slot_per_week > 2:
                        for t in range(math.ceil(needed_slot_per_week / 2)):
                            divide_value = (math.ceil(needed_slot_per_week / 2) - 1) * 12
                            if t != math.ceil(needed_slot_per_week / 2) - 1:
                                full_contact_hours -= divide_value
                                course["Contact hours"] = divide_value
                                list_courses_by_slot[c + "_" + str(t)] = course
                            else:
                                course1["Contact hours"] = full_contact_hours
                                list_courses_by_slot[c + "_" + str(t)] = course1
                    else:
                        list_courses_by_slot[c] = self.default_courses[c]
            else:
                for c in v:
                    list_courses_by_slot[c] = self.default_courses[c]
        return list_courses_by_slot
