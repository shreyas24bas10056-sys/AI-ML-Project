from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from .grid import Grid, Position
from . import search as search_mod

SearchFn = Callable[[Grid, Position, Position, int], Optional[List[Position]]]


ALGORITHMS = {
	"bfs": search_mod.bfs,
	"ucs": search_mod.ucs,
	"astar": search_mod.astar,
}


@dataclass
class AgentConfig:
	algo: str = "astar"
	hill_climb_attempts: int = 5
	hill_climb_neighbors: int = 12
	random_seed: Optional[int] = None


class DeliveryAgent:
	"""Agent that plans with BFS/UCS/A* and replans using hill-climbing with random restarts.

	Tracks path history and metrics for reporting.
	"""

	def __init__(self, grid: Grid, start: Position, goal: Position, config: Optional[AgentConfig] = None) -> None:
		self.grid = grid
		self.start = start
		self.goal = goal
		self.t = 0
		self.pos = start
		self.config = config or AgentConfig()
		if self.config.random_seed is not None:
			random.seed(self.config.random_seed)
		self._plan: List[Position] = []
		if self.config.algo not in ALGORITHMS:
			raise ValueError(f"Unknown algorithm: {self.config.algo}")
		self._search: SearchFn = ALGORITHMS[self.config.algo]
		# Metrics
		self.total_cost: int = 0
		self.steps_taken: int = 0
		self.replan_count: int = 0
		self.dynamic_conflicts: int = 0
		self.path_trace: List[Tuple[int, Position]] = [(self.t, self.pos)]
		self.last_action: str = "init"
		self.last_step_cost: int = 0
		self.last_reason: str = ""

	def planned_path(self) -> List[Position]:
		return list(self._plan)

	def at_goal(self) -> bool:
		return self.pos == self.goal

	def plan(self) -> bool:
		path = self._search(self.grid, self.pos, self.goal, self.t)
		if path is None or not path:
			self._plan = []
			return False
		# The returned path includes current position as first node; drop it for next steps
		self._plan = path[1:]
		return True

	def step(self) -> bool:
		"""Advance one time step. Returns True if moved or waited successfully, False if stuck."""
		if self.at_goal():
			return True
		# Ensure plan exists and remains valid for next step
		if not self._plan:
			if not self.plan():
				self.last_action = "stuck"
				self.last_reason = "no_initial_plan"
				return False
		replan_triggered = False
		next_pos = self._plan[0]
		next_t = self.t + 1
		# Treat dynamic obstacles as walls: if conflict now or at next tick -> replan
		if self.grid.is_blocked(next_pos, next_t) or self.grid.is_dynamic_blocked(next_pos, self.t):
			replan_triggered = True
			self.dynamic_conflicts += 1
			self.replan_count += 1
			# Force a full replan from current state
			if not self.plan():
				# Fallback to local hill-climb only if replanning fails
				if not self._local_hill_climb_move():
					self.last_action = "stuck"
					self.last_reason = "conflict_no_plan"
					return False
				self.last_action = "hill"
				self.last_reason = "conflict_fallback_hill"
				return True
			# After replanning, reassess next step
			next_pos = self._plan[0] if self._plan else self.pos
			next_t = self.t + 1
			if self.grid.is_blocked(next_pos, next_t) or self.grid.is_dynamic_blocked(next_pos, self.t):
				# Still blocked, try local hill climb once
				if not self._local_hill_climb_move():
					self.last_action = "stuck"
					self.last_reason = "conflict_after_replan"
					return False
				self.last_action = "hill"
				self.last_reason = "conflict_after_replan_hill"
				return True
		# Execute the move
		move_cost = 1 if next_pos == self.pos else self.grid.get_cost(next_pos)
		self.pos = next_pos
		self.t = next_t
		self.total_cost += move_cost
		self.steps_taken += 1
		self.path_trace.append((self.t, self.pos))
		self.last_step_cost = move_cost
		self.last_action = "wait" if next_pos == self.pos else "move"
		self.last_reason = "replan" if replan_triggered else "plan"
		# Drop the step just executed
		if self._plan and self._plan[0] == self.pos:
			self._plan.pop(0)
		return True

	def _local_hill_climb_move(self) -> bool:
		"""Local search for a feasible improving neighbor; may wait if best.

		Tries a set of candidate moves: neighbors at time t+1 that are not blocked,
		plus optionally staying in place if not blocked. Scores candidates by
		f = move_cost + Manhattan distance to goal, and picks the best. Performs
		random restarts by shuffling candidate evaluation order multiple times if
		no feasible improvement is found.
		"""
		attempts = max(1, self.config.hill_climb_attempts)
		for _ in range(attempts):
			candidates: List[Position] = []
			next_t = self.t + 1
			# Consider waiting
			if not self.grid.is_blocked(self.pos, next_t) and not self.grid.is_dynamic_blocked(self.pos, self.t):
				candidates.append(self.pos)
			# Consider moving
			for npos in self.grid.neighbors(self.pos, next_t):
				# Avoid swap collisions: skip if occupied now
				if self.grid.is_dynamic_blocked(npos, self.t):
					continue
				candidates.append(npos)
			if not candidates:
				continue
			random.shuffle(candidates)
			best_pos: Optional[Position] = None
			best_score = float("inf")
			for cand in candidates[: self.config.hill_climb_neighbors]:
				# Score: entering cost for move (1 if waiting) + heuristic to goal
				move_cost = 1 if cand == self.pos else self.grid.get_cost(cand)
				score = move_cost + search_mod.manhattan(cand, self.goal)
				if score < best_score:
					best_score = score
					best_pos = cand
			if best_pos is None:
				continue
			# Execute chosen local move
			move_cost = 1 if best_pos == self.pos else self.grid.get_cost(best_pos)
			self.pos = best_pos
			self.t = next_t
			self.total_cost += move_cost
			self.steps_taken += 1
			self.path_trace.append((self.t, self.pos))
			self.last_step_cost = move_cost
			self.last_action = "wait" if best_pos == self.pos else "move"
			self.last_reason = "hill"
			# Invalidate current plan; require replan from new state
			self._plan = []
			return True
		return False
