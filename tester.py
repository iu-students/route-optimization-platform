import json
import math


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_coords(point_id, depot, orders_by_id):
    """point_id == 0 -> depot, otherwise order id"""
    if point_id == 0:
        return depot['x'], depot['y']
    order = orders_by_id[point_id]
    return order['x'], order['y']


def euclidean(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def calc_cost(input_data, output_data):
    weights = input_data['weights']
    depot = input_data['depot']
    orders = input_data['orders']
    orders_by_id = {o['id']: o for o in orders}

    vehicles = output_data['vehicles']
    loaders = output_data['loaders']

    # --- 1. Стоимость машин (каждая использованная машина = одна "куплена") ---
    n_vehicles = len(vehicles)
    vehicles_cost = n_vehicles * weights['vehicle_salary']

    # --- 2. Стоимость грузчиков ---
    n_loaders = len(loaders)
    loaders_cost = n_loaders * weights['loader_salary']

    # --- 3. Топливо: суммарное расстояние всех машин ---
    total_distance = 0.0
    for v in vehicles:
        route = v['route']
        for a, b in zip(route[:-1], route[1:]):
            pa = get_coords(a, depot, orders_by_id)
            pb = get_coords(b, depot, orders_by_id)
            total_distance += euclidean(pa, pb)
    fuel_cost = total_distance * weights['fuel_cost']

    # --- 4. Работа грузчиков: суммарное время обслуживания заказов грузчиками ---
    total_loader_work_time = 0.0
    for l in loaders:
        for order_id in l['route']:
            order = orders_by_id[order_id]
            total_loader_work_time += order['loader_service_time']
    loader_work_cost = total_loader_work_time * weights['loader_work']

    # --- 5. Штраф за невыполненные опциональные заказы ---
    visited_orders = set()
    for v in vehicles:
        for point_id in v['route']:
            if point_id != 0:
                visited_orders.add(point_id)

    optional_orders = {o['id'] for o in orders if o.get('optional', 0) == 1}
    unfulfilled_optional = optional_orders - visited_orders
    optional_penalty_cost = len(unfulfilled_optional) * weights['optional_order_penalty']

    # --- 6. Проверка: обязательные заказы должны быть выполнены ---
    required_orders = {o['id'] for o in orders if o.get('optional', 0) == 0}
    missing_required = required_orders - visited_orders

    total_cost = (
        vehicles_cost
        + loaders_cost
        + fuel_cost
        + loader_work_cost
        + optional_penalty_cost
    )

    breakdown = {
        'n_vehicles': n_vehicles,
        'vehicles_cost': vehicles_cost,
        'n_loaders': n_loaders,
        'loaders_cost': loaders_cost,
        'total_distance': total_distance,
        'fuel_cost': fuel_cost,
        'total_loader_work_time': total_loader_work_time,
        'loader_work_cost': loader_work_cost,
        'n_unfulfilled_optional': len(unfulfilled_optional),
        'unfulfilled_optional_ids': sorted(unfulfilled_optional),
        'optional_penalty_cost': optional_penalty_cost,
        'missing_required_ids': sorted(missing_required),
        'total_cost': total_cost,
    }
    return breakdown


if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) == 3:
        input_path, output_path = sys.argv[1], sys.argv[2]
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_path = os.path.join(script_dir, 'data/input.json')
        output_path = os.path.join(script_dir, 'data/output.json')

    input_data = load_json(input_path)
    output_data = load_json(output_path)

    result = calc_cost(input_data, output_data)

    print('=== Разбивка стоимости решения ===')
    print(f"Машины: {result['n_vehicles']} x {input_data['weights']['vehicle_salary']} = {result['vehicles_cost']}")
    print(f"Грузчики: {result['n_loaders']} x {input_data['weights']['loader_salary']} = {result['loaders_cost']}")
    print(f"Суммарное расстояние: {result['total_distance']:.2f}")
    print(f"Топливо: {result['total_distance']:.2f} x {input_data['weights']['fuel_cost']} = {result['fuel_cost']:.2f}")
    print(f"Суммарное время работы грузчиков: {result['total_loader_work_time']}")
    print(f"Стоимость работы грузчиков: {result['total_loader_work_time']} x {input_data['weights']['loader_work']} = {result['loader_work_cost']}")
    print(f"Невыполненные опциональные заказы: {result['n_unfulfilled_optional']} {result['unfulfilled_optional_ids']}")
    print(f"Штраф за опциональные: {result['n_unfulfilled_optional']} x {input_data['weights']['optional_order_penalty']} = {result['optional_penalty_cost']}")
    if result['missing_required_ids']:
        print(f"!! ВНИМАНИЕ: пропущены обязательные заказы: {result['missing_required_ids']}")
    print('-----------------------------------')
    print(f"ИТОГО: {result['total_cost']:.2f}")