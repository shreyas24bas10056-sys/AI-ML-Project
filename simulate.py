from __future__ import annotations

import argparse
import random
import sys
from typing import List, Tuple

from delivery.grid import Grid, Position
from delivery.dynamic import MovingObstacle
from delivery.agent import DeliveryAgent, AgentConfig
from delivery import search as search_mod


def build_random_grid(width: int, height: int, seed: int) -> Grid:
	random.seed(seed)
	grid = Grid(width, height, default_cost=1)
	# Random terrain costs 1..5
	for y in range(height):
		for x in range(width):
			grid.set_cost((x, y), random.randint(1, 5))
	# Place static obstacles ~10%
	static: List[Position] = []
	for y in range(height):
		for x in range(width):
			if random.random() < 0.10:
				static.append((x, y))
	grid.set_static_obstacles(static)
	return grid


def add_dynamic_obstacles(grid: Grid, width: int, height: int, seed: int) -> None:
	random.seed(seed + 1)
	num = max(1, (width * height) // 60)
	for i in range(num):
		# Horizontal or vertical patrols
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
		grid.add_dynamic_obstacle(MovingObstacle(path=path, cycle=True))


def ensure_unblocked(grid: Grid, start: Position, goal: Position) -> None:
	# Clear static block at start/goal
	if grid.is_static_blocked(start):
		grid.set_static_obstacles({p for p in []})
	# The above cleared all; re-add without start/goal blocked is complicated here, so
	# instead we just ensure terrain cost is valid and rely on dynamics not occupying at t=0
	grid.remove_static_obstacle(start)
	grid.remove_static_obstacle(goal)
	grid.set_cost(start, max(1, grid.get_cost(start)))
	grid.set_cost(goal, max(1, grid.get_cost(goal)))


def run(args: argparse.Namespace) -> int:
	width = args.width
	height = args.height
	seed = args.seed
	algo = args.algo.lower()
	max_steps = args.steps
	print_every = args.print_every

	grid = build_random_grid(width, height, seed)
	add_dynamic_obstacles(grid, width, height, seed)

	start: Position = (0, 0)
	goal: Position = (width - 1, height - 1)
	ensure_unblocked(grid, start, goal)

	agent = DeliveryAgent(grid, start, goal, AgentConfig(algo=algo, random_seed=seed))

	print(f"Grid {width}x{height}, algo={algo}, seed={seed}")
	print(grid.render(agent.pos, goal, agent.t))
	print()

	for step in range(1, max_steps + 1):
		ok = agent.step()
		if step % print_every == 0 or agent.at_goal() or not ok:
			print(f"t={agent.t} pos={agent.pos} goal={goal} ok={ok}")
			print(grid.render(agent.pos, goal, agent.t))
			print()
		if not ok:
			print("Agent stuck; exiting.")
			return 2
		if agent.at_goal():
			print("Reached goal!")
			return 0
	return 1


def parse_args(argv: List[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Autonomous Delivery Agent Simulator")
	parser.add_argument("--algo", choices=["bfs", "ucs", "astar"], default="astar")
	parser.add_argument("--width", type=int, default=20)
	parser.add_argument("--height", type=int, default=12)
	parser.add_argument("--seed", type=int, default=7)
	parser.add_argument("--steps", type=int, default=400)
	parser.add_argument("--print-every", type=int, default=1)
	return parser.parse_args(argv)


if __name__ == "__main__":
	args = parse_args(sys.argv[1:])
	raise SystemExit(run(args)) 