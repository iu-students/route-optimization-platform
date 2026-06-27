from __future__ import annotations

import json
import os

import numpy as np
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
    point_id: int
    x: int
    y: int
    loader_cnt: int
    loader_service_time: int
    vehicle_time = 0.0
    end_time = 0.0
    vehicle: Vehicle
    point_available_time = 0.0
    urgency: float
    point_cost: float
    available_loaders: List[Loader]
    assigned_loaders: List[Loader]
    mandatory: bool

    def __init__(self, point_id: int, x: int, y: int, loader_service_time: int, vehicle: Vehicle, end_time: float,
                 vehicle_time: float, loader_cnt: int, mandatory: bool):
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
        self.mandatory = mandatory
        self.point_cost = 0.0
        self.assigned_loaders = []


class Loader:
    loader_home: Point
    loader_current_point: Point
    loader_shift_size: int
    loader_shift_time_left: int
    available_points: List[Point]
    loader_local_time: float
    route: List[Point]
    loader_full_salary: float
    loader_efficiency: float
    loader_profit: bool
    has_mandatory_point = False

    def __init__(self, loader_home: Point, loader_shift_size: int):
        self.loader_home = loader_home
        self.loader_shift_size = loader_shift_size
        self.available_points = []
        self.loader_shift_time_left = loader_shift_size
        self.loader_current_point = loader_home
        self.loader_local_time = loader_home.vehicle_time + self.loader_current_point.loader_service_time
        self.route = [loader_home]

    def work(self):
        self.loader_local_time += self.loader_current_point.loader_service_time

    @property
    def spawn_time(self) -> float:
        return self.loader_home.vehicle_time


# --- глобальное состояние ---
vehicles = []
unassigned_points = []
points = []
missed_points = []
loaders = []
loader_shift_size = 0
loader_speed = 0
loader_salary = 0
loader_work = 0
optional_point_penalty = 0
disadvantageous_points = []

convertion_dict = {}
distance_matrix = None


def reset_state():
    """Сбрасывает всё глобальное состояние перед повторным запуском."""
    global vehicles, unassigned_points, points, missed_points, loaders
    global disadvantageous_points, convertion_dict, distance_matrix
    vehicles = []
    unassigned_points = []
    points = []
    missed_points = []
    loaders = []
    disadvantageous_points = []
    convertion_dict = {}
    distance_matrix = None


def build_distance_matrix():
    global convertion_dict

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
    return distance_matrix[convertion_dict[p1.point_id]][convertion_dict[p2.point_id]]


def parse(data):
    for i in data["routes"]:
        v = Vehicle(i["id"], i["car_extra_time"])
        for j in i["points"]:
            current_point = Point(
                point_id=j["id"],
                x=j["x"],
                y=j["y"],
                loader_cnt=j["loader_cnt"],
                loader_service_time=j["loader_service_time"],
                vehicle_time=j["vehicle_time"],
                end_time=j["end_time"],
                vehicle=v,
                mandatory=j.get("mandatory", False)
            )
            v.vehicle_points.append(current_point)
            unassigned_points.append(current_point)
        vehicles.append(v)


def sort_points_by_vehicle_time(pts: List["Point"]) -> List["Point"]:
    return sorted(pts, key=lambda p: p.vehicle_time)


def find_available(loader: Loader):
    loader.available_points = []
    for i in unassigned_points:
        traveling_time = get_distance(loader.loader_current_point, i) / loader_speed
        traveling_home_time = get_distance(loader.loader_home, i) / loader_speed
        waiting_time = i.vehicle_time - loader.loader_local_time - traveling_time
        if (
                traveling_time + traveling_home_time + waiting_time + i.loader_service_time
        ) < loader.loader_shift_time_left and waiting_time >= 0:
            loader.available_points.append(i)
            if i in missed_points:
                missed_points.remove(i)
    loader.available_points = sort_points_by_vehicle_time(
        loader.available_points)


def find_the_earliest_point():
    the_earliest_point = missed_points[0]
    for i in missed_points:
        if i.vehicle_time < the_earliest_point.vehicle_time:
            the_earliest_point = i
    return the_earliest_point


def find_the_earliest_unassigned_point():
    the_earliest_point = unassigned_points[0]
    for i in unassigned_points:
        if i.vehicle_time < the_earliest_point.vehicle_time:
            the_earliest_point = i
    return the_earliest_point


def assign_loader_to_home_point(point: Point):
    point.loader_cnt -= 1
    if point.loader_cnt == 0 and point in unassigned_points:
        unassigned_points.remove(point)


def find_initial_distribution():
    while len(missed_points) > 0:
        the_earliest_point = find_the_earliest_point()
        loader = Loader(
            loader_home=the_earliest_point,
            loader_shift_size=loader_shift_size)
        missed_points.remove(the_earliest_point)
        assign_loader_to_home_point(the_earliest_point)
        loaders.append(loader)
        find_available(loader)


def move_loader_to(loader: Loader, point: Point):
    traveling_time = get_distance(loader.loader_current_point, point) / loader_speed
    waiting_time = max(0.0, point.vehicle_time - loader.loader_local_time - traveling_time)

    spent_time = traveling_time + waiting_time

    loader.loader_shift_time_left -= spent_time
    loader.loader_local_time += spent_time

    loader.loader_current_point = point
    loader.route.append(point)
    point.assigned_loaders.append(loader)

    loader.work()
    loader.loader_shift_time_left -= point.loader_service_time

    point.loader_cnt -= 1
    if point.loader_cnt == 0:
        if point in unassigned_points:
            unassigned_points.remove(point)


def return_loader_home(loader: Loader):
    traveling_home_time = get_distance(loader.loader_current_point, loader.loader_home) / loader_speed
    loader.loader_shift_time_left -= traveling_home_time
    loader.loader_local_time += traveling_home_time
    loader.loader_current_point = loader.loader_home
    loader.route.append(loader.loader_home)


def build_route_for_loader(loader: Loader):
    find_available(loader)
    while len(loader.available_points) > 0:
        next_point = loader.available_points[0]
        move_loader_to(loader, next_point)
        find_available(loader)

    return_loader_home(loader)


def calculate():
    find_initial_distribution()

    for loader in loaders:
        build_route_for_loader(loader)

    while len(unassigned_points) > 0:
        the_earliest_point = find_the_earliest_unassigned_point()
        loader = Loader(
            loader_home=the_earliest_point,
            loader_shift_size=loader_shift_size)
        loaders.append(loader)
        assign_loader_to_home_point(the_earliest_point)
        build_route_for_loader(loader)


def evaluate_disadvantageous(all_points: List[Point]):
    """
    Вычисляет point_cost для каждой точки и возвращает список невыгодных точек
    (не обязательных и дороже optional_point_penalty).
    """
    bad = []
    for i in all_points:
        i.point_cost = 0.0
        for j in i.assigned_loaders:
            if not j.has_mandatory_point:
                i.point_cost += i.loader_service_time * loader_work + loader_salary / max(len(j.route) - 1, 1)
                path_cost = 0.0
                if len(j.route) > 2:
                    idx = j.route.index(i)
                    if idx != 0:
                        path_cost = (
                            get_distance(j.route[idx - 1], i)
                            + get_distance(j.route[idx + 1], i)
                            - get_distance(j.route[idx - 1], j.route[idx + 1])
                        ) / loader_speed * loader_work
                i.point_cost += path_cost
        if i.point_cost >= optional_point_penalty and not i.mandatory:
            bad.append(i)
    return bad


def remove_disadvantageous_and_rerun(input_data: dict, bad_point_ids: set) -> dict:
    """
    Удаляет невыгодные точки из входного словаря данных и возвращает очищенную копию.
    Маршруты без точек после удаления тоже убираются.
    """
    cleaned = copy.deepcopy(input_data)
    new_routes = []
    removed_count = 0

    for route in cleaned["routes"]:
        new_points = [p for p in route["points"] if p["id"] not in bad_point_ids]
        removed_count += len(route["points"]) - len(new_points)
        if new_points:
            route["points"] = new_points
            new_routes.append(route)

    cleaned["routes"] = new_routes
    print(f"[rerun] Удалено невыгодных точек: {removed_count}, осталось маршрутов: {len(new_routes)}")
    return cleaned


def run_with_data(data: dict):
    """Инициализирует состояние из словаря данных и запускает расчёт."""
    global distance_matrix, missed_points, points

    reset_state()
    parse(data)
    distance_matrix = build_distance_matrix()
    missed_points = unassigned_points.copy()
    points = unassigned_points.copy()
    calculate()

    # помечаем грузчиков с обязательными точками
    for loader in loaders:
        loader.loader_full_salary = loader_salary + (loader_shift_size - loader_shift_time_left_snapshot(loader)) * loader_work
        for pt in loader.route:
            if pt.mandatory:
                loader.has_mandatory_point = True


def loader_shift_time_left_snapshot(loader: Loader) -> float:
    # loader_shift_time_left уже изменён в процессе, возвращаем как есть
    return loader.loader_shift_time_left


def solve_loaders():
    global loader_shift_size, loader_speed, loader_salary, loader_work, optional_point_penalty

    with open('loaders_task_list.json', 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    with open('input.json', 'r', encoding='utf-8') as f:
        cfg = json.load(f)
        loader_shift_size = cfg["loader_shift_size"]
        loader_speed = cfg["loader_speed"]
        loader_salary = cfg["weights"]["loader_salary"]
        loader_work = cfg["weights"]["loader_work"]
        optional_point_penalty = cfg["weights"]["optional_order_penalty"]

    current_data = input_data
    iteration = 1

    while True:
        print(f"[run {iteration}] Расчёт...")
        run_with_data(current_data)

        bad = evaluate_disadvantageous(points)
        print(f"[run {iteration}] Невыгодных точек: {len(bad)}")

        if not bad:
            print(f"[run {iteration}] Невыгодных точек нет, завершаем.")
            break

        bad_ids = {p.point_id for p in bad}
        print(f"[run {iteration}] ID невыгодных точек: {sorted(bad_ids)}")

        current_data = remove_disadvantageous_and_rerun(current_data, bad_ids)
        with open('loaders_task_list_cleaned.json', 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        print("[rerun] Очищенный файл сохранён: loaders_task_list_cleaned.json")

        iteration += 1

    return loaders


if __name__ == "__main__":
    solve_loaders()
    print(f"\nИтого грузчиков: {len(loaders)}")
    for loader in loaders:
        route_ids = [p.point_id for p in loader.route]
        print(f"  Грузчик (дом={loader.loader_home.point_id}): маршрут={route_ids}")
