from __future__ import annotations

from importlib.metadata import distribution

import numpy as np
import json
from typing import List


class Vehicle:
    # айди машины
    vehicle_id: int
    # точки у нее на маршруте
    vehicle_points: List[Point]
    # время до конца смены машины которое остается лишним после всех заказов
    free_time: float

    def __init__(self, vehicle_id: int, free_time: float):
        self.vehicle_id = vehicle_id
        self.free_time = free_time
        self.vehicle_points = []


class Point:
    # айди точки
    point_id: int
    # координаты
    x: int
    y: int
    # кол-во грузчиков на заказ
    loader_cnt: int
    # время котрое грузчики будт работать на этом заказе
    loader_service_time: int
    # время когда прибудет машина
    vehicle_time = 0.0
    # дедлайн по заказу
    end_time = 0.0
    # машина которая прибудет
    vehicle: Vehicle
    # время от момента прибытия машины до дедлайна (если вдруг придется бесцельно ждать на точке)
    point_available_time = 0.0
    # срочность точки
    urgency: float
    # потенциал движения в точку
    potential: float
    # все грузчики которые могут обработать заказ
    available_loaders: List[Loader]

    def __init__(self, point_id: int, x: int, y: int, loader_service_time: int, vehicle: Vehicle, end_time: float,
                 vehicle_time: float, loader_cnt: int):
        self.point_id = point_id
        self.x = x
        self.y = y
        self.loader_service_time = loader_service_time
        self.vehicle_time = vehicle_time
        self.end_time = end_time
        self.vehicle = vehicle
        self.point_available_time = end_time - vehicle_time
        self.loader_cnt = loader_cnt
        self.urgency = vehicle_time


class Loader:
    # домашняя точка (точка старта и конца смены)
    loader_home: Point
    # текущая точка
    loader_current_point: Point
    # длительность смены
    loader_shift_size: int
    # оставшееся время смены
    loader_shift_time_left: int
    # точки на которых грузчик еще успеет поработать (с учетом времени доезда до точки, работы и возврата домой)
    available_points: List[Point]
    # ремя на часах грузчика
    loader_local_time: float

    def __init__(self, loader_home: Point, loader_shift_size: int):
        self.loader_home = loader_home
        self.loader_shift_size = loader_shift_size
        self.available_points = []
        self.loader_shift_time_left = loader_shift_size
        self.loader_current_point = loader_home
        self.loader_local_time = loader_home.vehicle_time + self.loader_current_point.loader_service_time

    def work(self):
        self.loader_local_time += self.loader_current_point.loader_service_time


# хранит все автомобили
vehicles = []
# хранит все точки для котрых требуются грузчики
points = []
# хранит все точки которые еще не обработаны
missed_points = points.copy()
# хранит всех грузчиков
loaders = []
# хранит длительность смены грузчиков
loader_shift_size = 0
# хранит скорость грузчиков
loader_speed = 0

convertion_dict = {}

def build_distance_matrix():
    global convertion_dict

    # Заполняем словарь соответствия
    convertion_dict = {
        point.point_id: idx
        for idx, point in enumerate(points)
    }

    coords = np.array(
        [[point.x, point.y] for point in points],
        dtype=float
    )

    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    dist_matrix = np.sqrt((diff ** 2).sum(axis=2))

    return dist_matrix

distance_matrix = None


def get_distance(p1: Point, p2: Point):
    return distance_matrix[convertion_dict[p1.point_id]][convertion_dict[p2.point_id]]

def parse(data):
    for i in data["routes"]:
        v = Vehicle(i["id"], i["car_extra_time"])
        for j in i["points"]:
            current_point = Point(point_id=j["id"], x=j["x"], y=j["y"], loader_cnt=j["loader_cnt"],
                                  loader_service_time=j["loader_service_time"], vehicle_time=j["vehicle_time"],
                                  end_time=j["end_time"], vehicle=v)
            v.vehicle_points.append(current_point)
            points.append(current_point)
        vehicles.append(v)


# def sorting(points: List[Point]):

def find_available(loader: Loader):
    for i in points:
        traveling_time = get_distance(loader.loader_current_point, i) / loader_speed
        traveling_home_time = get_distance(loader.loader_home, i) / loader_speed
        waiting_time = i.vehicle_time - loader.loader_local_time + traveling_time
        if (traveling_time + traveling_home_time + waiting_time + i.loader_service_time) < loader.loader_shift_time_left and waiting_time >= 0:
            loader.available_points.append(i)
            i.available_loaders.append(loader)
            if i in missed_points:
                missed_points.remove(i)



# def assign_urgency():


def find_the_earliest_point():
    the_earliest_point = missed_points[0]
    for i in missed_points:
        if i.vehicle_time < the_earliest_point.vehicle_time:
            the_earliest_point = i
    return the_earliest_point


def find_initial_distribution():
    while len(missed_points) > 0:
        the_earliest_point = find_the_earliest_point()
        loader = Loader(loader_home=the_earliest_point, loader_shift_size=loader_shift_size)
        missed_points.remove(the_earliest_point)
        loaders.append(loader)
        find_available(loader)

def calculate():
    find_initial_distribution()





def solve_loaders():
    global loader_shift_size
    global loader_speed
    global distance_matrix
    global missed_points
    with open('loaders_task_list.json', 'r', encoding='utf-8') as loader_input:
        loader_input_data = json.load(loader_input)
        parse(loader_input_data)
        distance_matrix = build_distance_matrix()
        missed_points = points.copy()
    with open('input.json', 'r', encoding='utf-8') as input:
        input_data = json.load(input)
        loader_shift_size = input_data["loader_shift_size"]
        loader_speed = input_data["loader_speed"]
        calculate()
    print("ok")

solve_loaders()