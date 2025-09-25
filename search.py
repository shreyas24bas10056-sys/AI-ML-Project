from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from .grid import Grid, Position


@dataclass(frozen=True)
class State:
	pos: Position
	t: int


def manhattan(a: Position, b: Position) -> int:
	x1, y1 = a
	x2, y2 = b
	return abs(x1 - x2) + abs(y1 - y2)


def reconstruct_path(parent: Dict[State, Optional[State]], end: State) -> List[Position]:
	seq: List[Position] = []
	cur: Optional[State] = end
	while cur is not None:
		seq.append(cur.pos)
		cur = parent[cur]
	seq.reverse()
	return seq


def bfs(grid: Grid, start: Position, goal: Position, t0: int = 0, max_expansions: int = 200000) -> Optional[List[Position]]:
	"""Breadth-first search in time-expanded space with unit step costs.
	Includes a wait action with cost 1 per time step.
	"""
	if grid.is_blocked(start, t0):
		return None
	start_state = State(start, t0)
	frontier = deque([start_state])
	parent: Dict[State, Optional[State]] = {start_state: None}
	expanded = 0
	while frontier:
		cur = frontier.popleft()
		if cur.pos == goal:
			return reconstruct_path(parent, cur)
		expanded += 1
		if expanded > max_expansions:
			return None
		next_t = cur.t + 1
		# Wait
		if not grid.is_blocked(cur.pos, next_t):
			wait_state = State(cur.pos, next_t)
			if wait_state not in parent:
				parent[wait_state] = cur
				frontier.append(wait_state)
		# Moves
		for npos in grid.neighbors(cur.pos, next_t):
			ns = State(npos, next_t)
			if ns not in parent:
				parent[ns] = cur
				frontier.append(ns)
	return None


def ucs(grid: Grid, start: Position, goal: Position, t0: int = 0, max_expansions: int = 200000) -> Optional[List[Position]]:
	"""Uniform-cost search in time-expanded space.
	Cost to move = cost of entering cell; cost to wait = 1.
	"""
	if grid.is_blocked(start, t0):
		return None
	start_state = State(start, t0)
	frontier: List[Tuple[int, int, State]] = []
	heapq.heappush(frontier, (0, 0, start_state))
	g_cost: Dict[State, int] = {start_state: 0}
	parent: Dict[State, Optional[State]] = {start_state: None}
	expanded = 0
	counter = 1
	while frontier:
		cur_g, _, cur = heapq.heappop(frontier)
		if cur.pos == goal:
			return reconstruct_path(parent, cur)
		expanded += 1
		if expanded > max_expansions:
			return None
		next_t = cur.t + 1
		# Wait
		if not grid.is_blocked(cur.pos, next_t) and not grid.is_dynamic_blocked(cur.pos, cur.t):
			wait_state = State(cur.pos, next_t)
			new_g = cur_g + 1
			h = manhattan(wait_state.pos, goal)
			new_f = new_g + h
			prev_g = g_cost.get(wait_state)
			if prev_g is None or new_g < prev_g:
				g_cost[wait_state] = new_g
				parent[wait_state] = cur
				heapq.heappush(frontier, (new_f, counter, wait_state))
				counter += 1
		# Moves
		for npos in grid.neighbors(cur.pos, next_t):
			if grid.is_dynamic_blocked(npos, cur.t):
				continue
			move_cost = grid.get_cost(npos)
			ns = State(npos, next_t)
			new_g = cur_g + move_cost
			h = manhattan(npos, goal)
			new_f = new_g + h
			prev_g = g_cost.get(ns)
			if prev_g is None or new_g < prev_g:
				g_cost[ns] = new_g
				parent[ns] = cur
				heapq.heappush(frontier, (new_f, counter, ns))
				counter += 1
	return None


def astar(grid: Grid, start: Position, goal: Position, t0: int = 0, max_expansions: int = 200000) -> Optional[List[Position]]:
	"""A* in time-expanded space with Manhattan heuristic.
	Heuristic ignores time and dynamic obstacles; it is admissible if all costs >= 1.
	"""
	if grid.is_blocked(start, t0):
		return None
	start_state = State(start, t0)
	frontier: List[Tuple[int, int, State]] = []
	start_h = manhattan(start, goal)
	heapq.heappush(frontier, (start_h, 0, start_state))
	g_cost: Dict[State, int] = {start_state: 0}
	parent: Dict[State, Optional[State]] = {start_state: None}
	expanded = 0
	counter = 1
	while frontier:
		cur_f, _, cur = heapq.heappop(frontier)
		cur_g = g_cost[cur]
		if cur.pos == goal:
			return reconstruct_path(parent, cur)
		expanded += 1
		if expanded > max_expansions:
			return None
		next_t = cur.t + 1
		# Wait
		if not grid.is_blocked(cur.pos, next_t):
			wait_state = State(cur.pos, next_t)
			new_g = cur_g + 1
			h = manhattan(wait_state.pos, goal)
			new_f = new_g + h
			prev_g = g_cost.get(wait_state)
			if prev_g is None or new_g < prev_g:
				g_cost[wait_state] = new_g
				parent[wait_state] = cur
				heapq.heappush(frontier, (new_f, counter, wait_state))
				counter += 1
		# Moves
		for npos in grid.neighbors(cur.pos, next_t):
			if grid.is_dynamic_blocked(npos, cur.t):
				continue
			move_cost = grid.get_cost(npos)
			ns = State(npos, next_t)
			new_g = cur_g + move_cost
			h = manhattan(npos, goal)
			new_f = new_g + h
			prev_g = g_cost.get(ns)
			if prev_g is None or new_g < prev_g:
				g_cost[ns] = new_g
				parent[ns] = cur
				heapq.heappush(frontier, (new_f, counter, ns))
				counter += 1
	return None 