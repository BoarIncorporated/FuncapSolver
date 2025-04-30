import base64
import json
import math
import random
from typing import Dict, List, Tuple

import numpy as np

sqrt3 = np.sqrt(3)
sqrt5 = np.sqrt(5)


def wind_mouse(
    start_x: int,
    start_y: int,
    dest_x: int,
    dest_y: int,
    G_0: float = 9,
    W_0: float = 3,
    M_0: float = 15,
    D_0: float = 12,
    move_mouse: callable = lambda x, y: None,
) -> List[Tuple[int, int]]:
    current_x, current_y = start_x, start_y
    v_x = v_y = W_x = W_y = 0
    path: List[Tuple[int, int]] = [(current_x, current_y)]

    while (dist := np.hypot(dest_x - start_x, dest_y - start_y)) >= 1:
        W_mag = min(W_0, dist)
        if dist >= D_0:
            W_x = W_x / sqrt3 + (2 * np.random.random() - 1) * W_mag / sqrt5
            W_y = W_y / sqrt3 + (2 * np.random.random() - 1) * W_mag / sqrt5
        else:
            W_x /= sqrt3
            W_y /= sqrt3
            if M_0 < 3:
                M_0 = np.random.random() * 3 + 3
            else:
                M_0 /= sqrt5

        v_x += W_x + G_0 * (dest_x - start_x) / dist
        v_y += W_y + G_0 * (dest_y - start_y) / dist
        v_mag = np.hypot(v_x, v_y)

        if v_mag > M_0:
            v_clip = M_0 / 2 + np.random.random() * M_0 / 2
            v_x = (v_x / v_mag) * v_clip
            v_y = (v_y / v_mag) * v_clip

        start_x += v_x
        start_y += v_y
        move_x = int(np.round(start_x))
        move_y = int(np.round(start_y))

        if path[-1] != (move_x, move_y):
            path.append((move_x, move_y))

    return path


def resample_path(
    path: List[Tuple[int, int]], num_points: int = 18
) -> List[Tuple[int, int]]:
    pts = np.array(path, dtype=float)

    segment_lengths = np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))
    cumulative_lengths = np.concatenate(([0], np.cumsum(segment_lengths)))

    target_lengths = np.linspace(0, cumulative_lengths[-1], num_points)

    new_x = np.interp(target_lengths, cumulative_lengths, pts[:, 0])
    new_y = np.interp(target_lengths, cumulative_lengths, pts[:, 1])

    new_points = [(int(x), int(y)) for x, y in zip(new_x, new_y)]
    return new_points


def get_mouse_path(
    start_x: int, start_y: int, end_x: int, end_y: int
) -> List[Tuple[int, int]]:
    mouse_path = wind_mouse(start_x, start_y, end_x, end_y)
    mouse_path_sampled = resample_path(mouse_path, num_points=18)
    return mouse_path_sampled


def perlin_noise_1d(x: float, persistence: float = 0.5, octaves: int = 4) -> float:
    total = 0
    frequency = 1
    amplitude = 1
    for _ in range(octaves):
        total += interpolated_noise(x * frequency) * amplitude
        frequency *= 2
        amplitude *= persistence
    return total


def interpolated_noise(x: float) -> float:
    integer_x = int(x)
    fractional_x = x - integer_x
    v1 = smooth_noise(integer_x)
    v2 = smooth_noise(integer_x + 1)
    return cosine_interpolate(v1, v2, fractional_x)


def smooth_noise(x: int) -> float:
    return math.sin(x * 0.1) * random.uniform(-0.5, 0.5)


def cosine_interpolate(a: float, b: float, x: float) -> float:
    ft = x * 3.1415927
    f = (1 - math.cos(ft)) * 0.5
    return a * (1 - f) + b * f


class BioGenerator:
    def __init__(self):
        self.dPoints: List[Tuple[int, int]] = []
        self.timestamp: int = 0

    def binomial_coefficient(self, n: int, k: int) -> int:
        if k == 0 or k == n:
            return 1
        return self.binomial_coefficient(n - 1, k - 1) + self.binomial_coefficient(
            n - 1, k
        )

    def random_value(self, min_value: float, max_value: float) -> float:
        return random.uniform(min_value, max_value)

    def bezier_curve(
        self, points: List[Dict[str, float]], path: List[Dict[str, int]], timestamp: int
    ) -> int:
        num_points = len(points) - 1
        resolution = max(1, int(12 / len(self.dPoints) - self.random_value(0, 10)))

        for i in range(resolution + 1):
            t = (i / resolution) ** 2

            x, y = 0, 0
            for j in range(num_points + 1):
                binomial = (
                    self.binomial_coefficient(num_points, j)
                    * (1 - t) ** (num_points - j)
                    * t**j
                )
                x += points[j]["x"] * binomial
                y += points[j]["y"] * binomial

            x += self.random_value(-2, 6)
            y += self.random_value(-1, 7)

            if path:
                last_point = path[-1]
                # ∆x = x[t] - x[t-1]
                dx = x - last_point["x"]
                # ∆y = y[t] - y[t-1]
                dy = y - last_point["y"]

                # ∆t = t[t] - t[t-1]
                dt = timestamp - last_point["timestamp"]

                if dt > 0:
                    vx = dx / dt
                    vy = dy / dt
                    print(f"Velocity: vx = {vx:.2f}, vy = {vy:.2f}")

                distance_to_last_point = math.sqrt(dx**2 + dy**2)
            else:
                distance_to_last_point = 0

            if distance_to_last_point > 0.1 or not path:
                timestamp += int(self.random_value(80, 120))
                path.append(
                    {"timestamp": int(timestamp), "type": 0, "x": int(x), "y": int(y)}
                )

        return timestamp

    def generate_random_points(self, index: int) -> List[Dict[str, float]]:
        start = (
            [random.randint(260, 280), random.randint(200, 220)]
            if index == 0
            else self.dPoints[index - 1]
        )
        end = self.dPoints[index]

        midpoint_x = (start[0] + end[0]) / 2
        noise_scale = 0.17
        noise_offset = perlin_noise_1d(index * noise_scale) * 210
        midpoint_y = (start[1] + end[1]) / 2 + self.random_value(0, 210) + noise_offset

        return [
            {"x": start[0], "y": start[1]},
            {"x": midpoint_x, "y": midpoint_y},
            {"x": end[0], "y": end[1]},
        ]

    def generate_motion_data(self) -> str:
        self.timestamp = int(self.random_value(2300, 2400))
        motion_curve_data: List[Dict[str, int]] = []

        for i in range(9):
            control_points = self.generate_random_points(i)
            self.timestamp = self.bezier_curve(
                control_points, motion_curve_data, self.timestamp
            )

        out = []
        movement_index = [0, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 0, 1, 2]
        timestamp_change_index = {
            2: 1,
            3: 614,
            4: 1,
            5: 589,
            7: 549,
            8: 1,
            9: 1479,
            11: 521,
            13: 719,
            15: 2468,
            16: 1,
        }
        latest_timestamp = motion_curve_data[0]["timestamp"]
        starting_x, starting_y = random.randint(280, 300), random.randint(180, 200)
        ending_x, ending_y = random.randint(220, 230), random.randint(260, 270)
        mouse_points = get_mouse_path(starting_x, starting_y, ending_x, ending_y)

        for i, point in enumerate(motion_curve_data):
            vals = list(map(str, point.values()))
            vals[1] = str(movement_index[i])
            vals[2] = str(mouse_points[i][0])
            vals[3] = str(mouse_points[i][1])
            if i not in timestamp_change_index.keys():
                vals[0] = str(latest_timestamp)
            else:
                vals[0] = str(latest_timestamp + timestamp_change_index[i])
                latest_timestamp = int(vals[0])
            out.append(",".join(vals))

        return ";".join(out) + ";"

    def generate_d_points(self) -> List[Tuple[int, int]]:
        self.dPoints = []
        for _ in range(9):
            x, y = int(self.random_value(150, 327)), int(self.random_value(200, 480))
            self.dPoints.append((x, y))
        return self.dPoints

    @staticmethod
    def get_tbio_from_mbio(mbio: str) -> str:
        entries = [entry for entry in mbio.split(";") if entry]

        mbio_values = [
            (int(parts[0]), int(parts[2]), int(parts[3]))
            for entry in entries
            if (parts := entry.split(","))
        ]

        selected_indices = {0, 3, 5, 7, 9, 11, 13, 17}

        tbio_values = [
            f"{timestamp - random.randint(80, 100)},0,{x},{y}"
            for i, (timestamp, x, y) in enumerate(mbio_values)
            if i in selected_indices
        ]

        return ";".join(tbio_values) + ";"

    def generate(self) -> str:
        self.dPoints = self.generate_d_points()
        motion_data = self.generate_motion_data()
        touch_data = self.get_tbio_from_mbio(motion_data)

        data = {"mbio": motion_data, "tbio": touch_data, "kbio": ""}

        data_json = json.dumps(data, separators=(",", ":"))
        return base64.b64encode(data_json.encode("utf-8")).decode("utf-8")


if __name__ == "__main__":
    data = BioGenerator()
    print(data.generate())
