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
        self.generations = 500
        self.crossover_probability = 0.8
        self.mutation_probability = 0.2
        self.courses = self.hard_constraints.get_courses()
        self.rooms = self.hard_constraints.get_rooms()

    def generate_timetable(self):
        new_courses = devide_courses_to_slot(self.courses)
        rooms = self.hard_constraints.get_rooms()
        free_timeslots = self.hard_constraints.get_free_timeslots()
        self.create_population()
        pop = self.population
        final_idx = 0
        count = 1

        while self.fitness(pop[final_idx]) < 63 and count < self.generations:
            list_fitness_pop = []
            for i in pop:
                score = self.fitness(i)
                list_fitness_pop.append(score)
            parent1, parent2, par1_idx, par2_idx = self.selection(list_fitness_pop)
            new_ind = self.crossover(parent1, parent2)
            new_ind = self.mutation(new_ind)
            if self.fitness(new_ind) > self.fitness(pop[np.argmin(list_fitness_pop)]):
                pop[np.argmin(list_fitness_pop)] = new_ind
            final_idx = np.argmax(list_fitness_pop)

            count += 1
            print("gen {} best fit: {} rate {:.2f}%".format(
                count, self.fitness(pop[final_idx]), self.fitness(pop[final_idx]) / 63 * 100))
            if np.argmin(list_fitness_pop) == np.argmax(list_fitness_pop):
                break
        print("done!")
        result = pop[final_idx]
        result = result.reshape(20, 8)
        return result

    def crossover(self, individual1, individual2):
        individual1_new = individual1.copy()
        individual2_new = individual2.copy()

        for i in range(self.individual_size):
            if random.random() < self.crossover_probability and int(individual2_new[i]) != 0:
                # find course id to crossover
                ind1_idx = np.where(individual1_new == individual2_new[i])[0][0]
                ind1_course_id = individual1_new[i]

                individual1_new[i] = individual2_new[i]
                individual1_new[ind1_idx] = ind1_course_id
        # if self.fitness(individual1_new) > self.fitness(individual2_new):
        #     return individual1_new
        # else:
        #     return individual2_new
        return individual1_new

    def mutation(self, individual):
        individual_m = individual.copy()
        for i in range(self.individual_size):
            if random.random() < self.mutation_probability and individual_m[i] != 0:
                courses_idx = np.where(individual_m != 0)
                while True:
                    slected_id = random.randint(1, len(courses_idx[0]))
                    if slected_id != individual_m[i]:
                        break
                m_id = individual_m[i]
                individual_m[i] = slected_id
                courses_m_idx = np.where(individual_m == slected_id)[0][0]
                individual_m[courses_m_idx] = m_id
        return individual_m

    def selection_old(self, population, list_fitness_pop):
        index1 = random.randint(0, self.population_size - 1)
        while True:
            index2 = random.randint(0, self.population_size - 1)
            index3 = random.randint(0, self.population_size - 1)
            index4 = random.randint(0, self.population_size - 1)
            if index4 != index3 != index2 != index1:
                break
        # parent 1
        par1_idx = index1
        parent1 = population[index1]
        if list_fitness_pop[index2] > list_fitness_pop[index1]:
            par1_idx = index2
            parent1 = population[index2]

        # parent 2
        par2_idx = index3
        parent2 = population[index3]
        if list_fitness_pop[index4] > list_fitness_pop[index3]:
            par1_idx = index4
            parent2 = population[index4]

        return parent1, parent2, par1_idx, par2_idx

    def selection(self, list_fitness_pop):
        population = self.population
        l = np.array(list_fitness_pop)
        par1_idx, par2_idx = l.argsort()[-2:][::-1]
        parent1 = population[par1_idx]
        parent2 = population[par2_idx]

        # par = l.argsort()[-4:][::-1]
        # parent1 = population[par[2]]
        # parent2 = population[par[3]]

        return parent1, parent2, par1_idx, par2_idx

        # return parent1, parent2, par[2], par[3]

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
                if c["Number of students"] >= r["Capacity"]:
                    score += 1
                # lecturers constraint
                if not has_lecturer_conflict(g, count, individual, courses):
                    score += 1
                # slot constraint
                if not has_slot_conflict(g, count, individual, courses):
                    score += 1
                # start at 11pm
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
def has_slot_conflict(gen, pos, individual, courses):
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

    # for i in range(start_slot, end_slot + 1, 8):
    #     another_gen_id = list_courses[i -1]
    #     if another_gen_id:
    #         return True

    return False


# course with 36h or 34h occupies 3 slots/week
# course with 20h or 22h occupies 2 slots/w
# course with 12h occupies 1 slot/w
# total 58/160 slots/week
def devide_courses_to_slot(courses):
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
