from __future__ import annotations

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
    # время от прибытия машины до дедлайна (если придется ждать на точке)
    point_available_time = 0.0
    # срочность точки
    urgency: float
    # потенциал движения в точку
    potential: float
    # все грузчики которые могут обработать заказ
    available_loaders: List[Loader]

    def __init__(
        self, point_id: int, x: int, y: int, loader_service_time: int,
        vehicle: Vehicle, end_time: float, vehicle_time: float, loader_cnt: int,
    ):
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
    # точки, где грузчик еще успеет поработать (с учетом времени доезда, работы и возврата)
    available_points: List[Point]
    # время на часах грузчика
    loader_local_time: float
    # построенный маршрут (последовательность точек, которые грузчик посещает)
    route: List[Point]

    def __init__(self, loader_home: Point, loader_shift_size: int):
        self.loader_home = loader_home
        self.loader_shift_size = loader_shift_size
        self.available_points = []
        self.loader_shift_time_left = loader_shift_size
        self.loader_current_point = loader_home
        # грузчик спавнится в момент прибытия машины в его домашнюю точку
        # и сразу же отрабатывает на ней
        self.loader_local_time = (
            loader_home.vehicle_time + self.loader_current_point.loader_service_time
        )
        self.route = [loader_home]

    def work(self):
        self.loader_local_time += self.loader_current_point.loader_service_time

    @property
    def spawn_time(self) -> float:
        # время спавна грузчика = время прибытия машины в его домашнюю точку
        return self.loader_home.vehicle_time


# хранит все автомобили
vehicles = []
# хранит все точки для котрых требуются грузчики
unassigned_points = []
# хранит все точки которые еще не обработаны
missed_points = unassigned_points.copy()
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
        for idx, point in enumerate(unassigned_points)
    }

    coords = np.array(
        [[point.x, point.y] for point in unassigned_points],
        dtype=float
    )

    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    dist_matrix = np.sqrt((diff ** 2).sum(axis=2))

    return dist_matrix


distance_matrix = None


def get_distance(p1: Point, p2: Point):
    return distance_matrix[
        convertion_dict[p1.point_id]
    ][
        convertion_dict[p2.point_id]
    ]


def parse(data):
    for i in data["routes"]:
        v = Vehicle(i["id"], i["car_extra_time"])
        for j in i["points"]:
            current_point = Point(
                point_id=j["id"], x=j["x"], y=j["y"], loader_cnt=j["loader_cnt"],
                loader_service_time=j["loader_service_time"],
                vehicle_time=j["vehicle_time"],
                end_time=j["end_time"], vehicle=v,
            )
            v.vehicle_points.append(current_point)
            unassigned_points.append(current_point)
        vehicles.append(v)


def sort_points_by_vehicle_time(points: List["Point"]) -> List["Point"]:
    """
    Сортирует точки по времени прибытия машины (vehicle_time) по возрастанию.
    Возвращает новый отсортированный список.
    """
    return sorted(points, key=lambda p: p.vehicle_time)


def find_available(loader: Loader):
    """Пересчитывает available_points грузчика на основе unassigned_points
    и текущего положения/времени (loader_current_point, loader_local_time)."""
    loader.available_points = []
    for i in unassigned_points:
        travel_time = get_distance(loader.loader_current_point, i) / loader_speed
        home_time = get_distance(loader.loader_home, i) / loader_speed
        wait = i.vehicle_time - loader.loader_local_time - travel_time
        total = travel_time + home_time + wait + i.loader_service_time
        if total < loader.loader_shift_time_left and wait >= 0:
            loader.available_points.append(i)
            if i in missed_points:
                missed_points.remove(i)
    loader.available_points = sort_points_by_vehicle_time(
        loader.available_points
    )


def find_the_earliest_point():
    the_earliest_point = missed_points[0]
    for i in missed_points:
        if i.vehicle_time < the_earliest_point.vehicle_time:
            the_earliest_point = i
    return the_earliest_point


def find_the_earliest_unassigned_point():
    """
    Аналог find_the_earliest_point, но ищет по unassigned_points
    (используется при создании дополнительных грузчиков после первой фазы).
    """
    the_earliest_point = unassigned_points[0]
    for i in unassigned_points:
        if i.vehicle_time < the_earliest_point.vehicle_time:
            the_earliest_point = i
    return the_earliest_point


def assign_loader_to_home_point(point: Point):
    """
    Учитывает, что новый грузчик сам обрабатывает свою домашнюю точку:
    уменьшает loader_cnt этой точки и убирает ее из unassigned_points,
    если она полностью обработана.
    """
    point.loader_cnt -= 1
    if point.loader_cnt == 0 and point in unassigned_points:
        unassigned_points.remove(point)


def find_initial_distribution():
    while len(missed_points) > 0:
        the_earliest_point = find_the_earliest_point()
        loader = Loader(
            loader_home=the_earliest_point,
            loader_shift_size=loader_shift_size,
        )
        missed_points.remove(the_earliest_point)
        assign_loader_to_home_point(the_earliest_point)
        loaders.append(loader)
        find_available(loader)


def move_loader_to(loader: Loader, point: Point):
    """
    Перемещает грузчика на point: обновляет текущее положение, время и
    оставшееся время смены, отрабатывает заказ и уменьшает loader_cnt точки.
    Если loader_cnt точки дошел до 0, точка убирается из unassigned_points.
    """
    travel_time = get_distance(loader.loader_current_point, point) / loader_speed
    waiting_time = max(
        0.0, point.vehicle_time - loader.loader_local_time - travel_time
    )

    spent_time = traveling_time + waiting_time

    loader.loader_shift_time_left -= spent_time
    loader.loader_local_time += spent_time

    loader.loader_current_point = point
    loader.route.append(point)

    loader.work()
    loader.loader_shift_time_left -= point.loader_service_time

    point.loader_cnt -= 1
    if point.loader_cnt == 0:
        if point in unassigned_points:
            unassigned_points.remove(point)


def return_loader_home(loader: Loader):
    """
    Добавляет в маршрут возврат на домашнюю точку. Грузчик там не работает
    (он уже отработал на ней в момент своего появления), просто едет туда.
    """
    home_time = get_distance(
        loader.loader_current_point, loader.loader_home
    ) / loader_speed
    loader.loader_shift_time_left -= traveling_home_time
    loader.loader_local_time += traveling_home_time
    loader.loader_current_point = loader.loader_home
    loader.route.append(loader.loader_home)


def build_route_for_loader(loader: Loader):
    """
    Жадно строит маршрут для одного грузчика:
    на каждом шаге берет самую срочную (минимальный vehicle_time) точку
    из available_points, едет туда, заново пересчитывает available_points
    из unassigned_points, и так пока available_points не опустеет.
    В конце добавляет возврат домой.
    """
    find_available(loader)
    while len(loader.available_points) > 0:
        next_point = loader.available_points[0]  # уже отсортированы
        move_loader_to(loader, next_point)
        find_available(loader)

    return_loader_home(loader)


def calculate():
    find_initial_distribution()

    # строим маршруты для всех изначально созданных грузчиков
    for loader in loaders:
        build_route_for_loader(loader)

    # пока остаются необработанные точки (кроме случая когда осталась
    # только условная "точка дома", т.е. список пуст) - создаем новых грузчиков
    while len(unassigned_points) > 0:
        the_earliest_point = find_the_earliest_unassigned_point()
        loader = Loader(
            loader_home=the_earliest_point,
            loader_shift_size=loader_shift_size,
        )
        loaders.append(loader)

        # домашняя точка нового грузчика обрабатывается им самим
        assign_loader_to_home_point(the_earliest_point)

        build_route_for_loader(loader)


def solve_loaders():
    global loader_shift_size
    global loader_speed
    global distance_matrix
    global missed_points
    with open('loaders_task_list.json', 'r', encoding='utf-8') as loader_input:
        loader_input_data = json.load(loader_input)
        parse(loader_input_data)
        if not unassigned_points:
            return []
        distance_matrix = build_distance_matrix()
        missed_points = unassigned_points.copy()
    with open('input.json', 'r', encoding='utf-8') as input:
        input_data = json.load(input)
        loader_shift_size = input_data["loader_shift_size"]
        loader_speed = input_data["loader_speed"]
        calculate()
    return loaders


def clear_loaders_state():
    vehicles.clear()
    unassigned_points.clear()
    missed_points.clear()
    loaders.clear()


if __name__ == "__main__":
    solve_loaders()
    print("ok")
