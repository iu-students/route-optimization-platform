import pytest
import loaders


@pytest.fixture(autouse=True)
def reset_state():
    loaders.clear_loaders_state()
    loaders.distance_matrix = None
    loaders.convertion_dict = {}
    loaders.loader_speed = 0
    loaders.loader_shift_size = 0
    yield
    loaders.clear_loaders_state()


def test_point_fields():
    p = loaders.Point(point_id=1, x=0, y=0, loader_service_time=5,
                      vehicle=None, end_time=30, vehicle_time=10, loader_cnt=2)
    assert p.point_available_time == 20
    assert p.urgency == 10


def test_sort_by_vehicle_time():
    p1 = loaders.Point(1, 0, 0, 5, None, 30, 30, 1)
    p2 = loaders.Point(2, 0, 0, 5, None, 30, 10, 1)
    p3 = loaders.Point(3, 0, 0, 5, None, 30, 20, 1)
    ordered = loaders.sort_points_by_vehicle_time([p1, p2, p3])
    assert [p.vehicle_time for p in ordered] == [10, 20, 30]


def test_distance_matrix():
    data = {"routes": [{
        "id": 1, "car_extra_time": 100,
        "points": [
            {"id": 1, "x": 0, "y": 0, "loader_cnt": 1, "loader_service_time": 5,
             "vehicle_time": 0, "end_time": 100},
            {"id": 2, "x": 3, "y": 4, "loader_cnt": 1, "loader_service_time": 5,
             "vehicle_time": 0, "end_time": 100},
        ],
    }]}
    loaders.parse(data)
    loaders.distance_matrix = loaders.build_distance_matrix()

    p1, p2 = loaders.unassigned_points[0], loaders.unassigned_points[1]
    assert loaders.get_distance(p1, p2) == pytest.approx(5.0)
    assert loaders.get_distance(p1, p1) == pytest.approx(0.0)


def test_full_calculate_serves_all_points():
    data = {"routes": [{
        "id": 1, "car_extra_time": 100,
        "points": [
            {"id": 1, "x": 0, "y": 0, "loader_cnt": 1, "loader_service_time": 5,
             "vehicle_time": 0, "end_time": 100},
            {"id": 2, "x": 1, "y": 0, "loader_cnt": 1, "loader_service_time": 5,
             "vehicle_time": 10, "end_time": 100},
        ],
    }]}
    loaders.parse(data)
    loaders.distance_matrix = loaders.build_distance_matrix()
    loaders.missed_points = loaders.unassigned_points.copy()
    loaders.loader_speed = 1
    loaders.loader_shift_size = 1000

    loaders.calculate()

    assert len(loaders.unassigned_points) == 0
    assert len(loaders.loaders) >= 1


def test_clear_state():
    data = {"routes": [{
        "id": 1, "car_extra_time": 100,
        "points": [{"id": 1, "x": 0, "y": 0, "loader_cnt": 1,
                    "loader_service_time": 5, "vehicle_time": 0, "end_time": 100}],
    }]}
    loaders.parse(data)
    assert len(loaders.unassigned_points) == 1
    loaders.clear_loaders_state()
    assert len(loaders.unassigned_points) == 0
    assert len(loaders.vehicles) == 0
