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

"""
idea:
1. initialization population (instance timetable), each gene contains room information(capacity,room id) and course information(subject, num of students, teachers)
2. calculate fitness function for each individual from population based on constraints.
3. select pair of parents to crossover new child.
4. the new child is then undergone throung mution.
5. iteration the loop until find feasible timetable.

"""


class Genetic(Scheduler):
    def __init__(self):
        super().__init__()
        self.population = []
        self.population_size = 250
        self.individual_size = 20 * 8
        self.generations = 250
        self.crossover_probability = 0.5
        self.mutation_probability = 0.2
        self.rooms = self.hard_constraints.get_rooms()
        self.courses = self.hard_constraints.get_courses()
        self.timeslots = self.hard_constraints.get_free_timeslots()
        # self.courses = divide_courses_to_slot(self.hard_constraints.get_courses())

    def generate_timetable(self):
        self.create_population()
        pop = self.population
        final_idx = 0
        count = 1

        # no divide =21; divide =58
        max_fit = 4 * 21
        # stop when satisfying all hard constraints or reach generation 500th
        while self.fitness(pop[final_idx]) < max_fit and count < self.generations:
            list_fitness_pop = []
            for i in pop:
                score = self.fitness(i)
                list_fitness_pop.append(score)

            # TODO: test only remove for when done
            for i in range(1):
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
            print("gen {} best fit: {} rate {:.2f}%".format(
                count, self.fitness(pop[final_idx]), self.fitness(pop[final_idx]) / max_fit * 100))
            if np.argmin(list_fitness_pop) == np.argmax(list_fitness_pop):
                break
        print("done!")
        print("fail {}".format(max_fit - self.fitness(pop[final_idx])))
        result = pop[final_idx]
        result = fill_timeslot(result, self.courses)
        result = self.convert_to_schedule(result)
        self.copy_schedule(result)

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

    # TODO: test only remove when done
    # mutation without freeslot
    def mutation1(self, individual):
        individual_m = individual.copy()
        for i in range(self.individual_size):
            if random.random() < self.mutation_probability and individual_m[i] != 0:
                courses_id = np.where(individual_m != 0)
                while True:
                    slected_id = random.randint(1, len(courses_id[0]))
                    if slected_id != individual_m[i]:
                        break
                m_id = individual_m[i]
                individual_m[i] = slected_id
                courses_m_idx = np.where(individual_m == slected_id)[0][0]
                individual_m[courses_m_idx] = m_id
        return individual_m

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

    def fitness(self, individual):
        courses = self.courses
        rooms = self.rooms
        list_courses = list(courses)
        lis_rooms = list(rooms)
        count = 0
        score = 0
        for g in individual:
            if g != 0:
                c = courses[list_courses[int(g) - 1]]
                r = rooms[lis_rooms[count % 8]]
                s = math.floor(count / 8)
                # room capacity constraint
                if c["Number of students"] <= r["Capacity"]:
                    score += 1
                # lecturers constraint
                if not has_lecturer_conflict(g, count, individual, courses):
                    score += 1
                # slot constraint
                if not has_slot_conflict(g, count, courses):
                    score += 1
                # room constraint
                if not has_room_conflict(g, count, courses, individual):
                    score += 1
                # start at 11pm (soft constraint)
                # if s == 2:
                #     score += 1
            count += 1
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
                    course = self.courses[course_id]
                    prog_id = course["Programme"]
                    room_id = list_rooms[c_room]
                    self.schedule.setdefault(str(self.timeslots[count]), []).append(
                        {"CourseID": course_id, "ProgID": prog_id, "RoomID": room_id})
                    schedule_result.setdefault(self.timeslots[count], []).append(
                        {"CourseID": course_id, "ProgID": prog_id, "RoomID": room_id})
                    course['Contact hours'] -= 2
                c_room += 1
            count += 1
            c_room = 0
        return schedule_result

    def copy_schedule(self, schedule):
        period_end = self.hard_constraints.period_info["EndDate"]
        week_counter = 1
        first_lecture = next(iter(schedule.keys()))
        courses = self.hard_constraints.get_courses()
        while first_lecture + timedelta(days=7 * week_counter) < period_end:
            for date, scheduled_courses in schedule.items():
                date = date + timedelta(days=7 * week_counter)

                for course in scheduled_courses:
                    course_id = course["CourseID"]
                    self.schedule.setdefault(str(date), []).append(
                        {"CourseID": course_id, "ProgID": course["ProgID"], "RoomID": course["RoomID"]})
                    courses[course_id]['Contact hours'] -= 2
            week_counter += 1


# check lecture conflict in slot time of day
# gen = class
def has_lecturer_conflict(gen, pos, individual, courses):
    list_courses = list(courses)
    # low,high = row
    low_slot = pos - (pos % 8)
    high_slot = pos - (pos % 8) + 8

    gen_course = courses[list_courses[int(gen) - 1]]
    lecturers = gen_course["Lecturers"].split(';')

    for g in individual[low_slot:high_slot]:
        if g != 0 and g != gen:
            c = courses[list_courses[int(g) - 1]]
            list_lecturers = c["Lecturers"].split(';')
            for l in list_lecturers:
                if l in lecturers:
                    return True
    return False


# if course slots =18 or 17 set full slot per day
def has_slot_conflict(gen, pos, courses):
    list_courses = list(courses)
    # start, end = column
    # 32 slots per day
    start_slot = (pos % 8) + math.floor(pos / 32) * 32
    end_slot = start_slot + 24

    gen_course_id = list_courses[int(gen) - 1]
    gen_course = courses[gen_course_id]

    contact_hours = int(gen_course["Contact hours"] / 2)
    needed_slot_per_week = math.ceil(contact_hours / 7)
    if (pos + 8 * (needed_slot_per_week - 1)) > end_slot:
        return True
    return False


# check room conflict in same day
def has_room_conflict(gen, pos, courses, individual):
    list_courses = list(courses)
    # start, end = column
    # 32 slots per day
    start_slot = (pos % 8) + math.floor(pos / 32) * 32
    end_slot = start_slot + 24

    gen_course_id = list_courses[int(gen) - 1]
    gen_course = courses[gen_course_id]

    contact_hours = int(gen_course["Contact hours"] / 2)
    needed_slot_per_week = math.ceil(contact_hours / 7)
    for i in range(pos + 8, end_slot + 1, 8):
        needed_slot_per_week -= 1
        if individual[i] != 0 and needed_slot_per_week != 0:
            return True
    return False


def fill_timeslot(data, courses):
    list_courses = list(courses)
    new_timetable = data.copy()
    for idx, value in enumerate(data):
        if value != 0:
            start_slot = (idx % 8) + math.floor(idx / 32) * 32
            end_slot = start_slot + 24
            gen_course_id = list_courses[int(value) - 1]
            gen_course = courses[gen_course_id]
            contact_hours = int(gen_course["Contact hours"] / 2)
            needed_slot_per_week = math.ceil(contact_hours / 7)
            for i in range(idx + 8, end_slot + 1, 8):
                needed_slot_per_week -= 1
                if new_timetable[i] == 0 and needed_slot_per_week != 0:
                    new_timetable[i] = value
                elif new_timetable[i] != 0:
                    break
    return new_timetable


# course with 36h or 34h occupies 3 slots/week
# course with 20h or 22h occupies 2 slots/w
# course with 12h occupies 1 slot/w
# total 58/160 slots/week
# TODO: currently not use
def divide_courses_to_slot(courses):
    list_courses_by_slot = {}
    for k, v in courses.items():
        # 2 hours/timeslot
        contact_hours = int(v["Contact hours"] / 2)
        # 7 weeks/ period
        needed_slot_per_week = math.ceil(contact_hours / 7)
        if needed_slot_per_week == 1:
            list_courses_by_slot[k] = v
        else:
            for t in range(needed_slot_per_week):
                list_courses_by_slot[k + "_" + str(t)] = v
    return list_courses_by_slot
