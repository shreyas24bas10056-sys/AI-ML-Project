from __future__ import annotations

import time
import random
from typing import Dict, List, Tuple

from delivery.grid import Grid, Position
from delivery.dynamic import MovingObstacle
from delivery import search

ALGOS = [
	("bfs", search.bfs),
	("ucs", search.ucs),
	("astar", search.astar),
]


def make_grid(width: int, height: int, seed: int) -> Grid:
	random.seed(seed)
	g = Grid(width, height, default_cost=1)
	for y in range(height):
		for x in range(width):
			g.set_cost((x, y), random.randint(1, 5))
	# ~10% walls
	walls = []
	for y in range(height):
		for x in range(width):
			if random.random() < 0.10:
				walls.append((x, y))
	g.set_static_obstacles(walls)
	# add some dynamic obstacles
	num_dyn = max(1, (width * height) // 60)
	for _ in range(num_dyn):
		if random.random() < 0.5:
			y = random.randint(0, height - 1)
			path = [(x, y) for x in range(width)]
			if random.random() < 0.5:
				path.reverse()
		else:
			x = random.randint(0, width - 1)
			path = [(x, y) for y in range(height)]
			if random.random() < 0.5:
				path.reverse()
		g.add_dynamic_obstacle(MovingObstacle(path=path, cycle=True))
	return g


def run_once(width: int, height: int, seed: int) -> List[Dict[str, float]]:
	g = make_grid(width, height, seed)
	start: Position = (0, 0)
	goal: Position = (width - 1, height - 1)
	if g.is_static_blocked(start):
		g.remove_static_obstacle(start)
	if g.is_static_blocked(goal):
		g.remove_static_obstacle(goal)
	results: List[Dict[str, float]] = []
	for name, fn in ALGOS:
		start_time = time.perf_counter()
		path = fn(g, start, goal, 0)
		elapsed_ms = (time.perf_counter() - start_time) * 1000
		path_cost = 0
		if path:
			for i in range(1, len(path)):
				prev = path[i - 1]
				nxt = path[i]
				path_cost += 1 if nxt == prev else g.get_cost(nxt)
		results.append({
			"algo": name,
			"seed": seed,
			"width": width,
			"height": height,
			"time_ms": elapsed_ms,
			"path_len": len(path) if path else 0,
			"path_cost": path_cost,
			"found": 1 if path else 0,
		})
	return results


def main() -> None:
	width, height = 20, 12
	seeds = [3, 5, 7, 11, 13]
	rows: List[Dict[str, float]] = []
	for s in seeds:
		rows.extend(run_once(width, height, s))
	# Aggregate by algo
	summary: Dict[str, Dict[str, float]] = {}
	for r in rows:
		name = r["algo"]
		acc = summary.setdefault(name, {"n": 0, "time_ms": 0.0, "path_len": 0.0, "path_cost": 0.0, "found": 0.0})
		acc["n"] += 1
		acc["time_ms"] += r["time_ms"]
		acc["path_len"] += r["path_len"]
		acc["path_cost"] += r["path_cost"]
		acc["found"] += r["found"]
	# Write REPORT.md
	lines: List[str] = []
	lines.append("# Project Report\n")
	lines.append("## Experimental Results (average over seeds)\n")
	lines.append("Algorithm | Found% | Avg Time (ms) | Avg Path Len | Avg Path Cost")
	lines.append("--- | ---:| ---:| ---:| ---:")
	for name, acc in summary.items():
		n = max(1, int(acc["n"]))
		found_pct = 100.0 * acc["found"] / n
		lines.append(f"{name} | {found_pct:.0f}% | {acc['time_ms']/n:.1f} | {acc['path_len']/n:.1f} | {acc['path_cost']/n:.1f}")
	lines.append("\n(Computed on random 20x12 grids with terrain costs, ~10% static walls, and a few dynamic obstacles.)\n")
	with open("REPORT.md", "w", encoding="utf-8") as f:
		f.write("\n".join(lines))
	print("Wrote REPORT.md")


if __name__ == "__main__":
	main() 