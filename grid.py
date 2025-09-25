from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Set, Tuple

Position = Tuple[int, int]


@dataclass(frozen=True)
class Bounds:
	width: int
	height: int

	def in_bounds(self, pos: Position) -> bool:
		x, y = pos
		return 0 <= x < self.width and 0 <= y < self.height


class Grid:
	"""2D grid with terrain costs, static and dynamic obstacles.

	- Movement cost is the cost of entering a cell (>= 1)
	- Static obstacles are impassable
	- Dynamic obstacles are time-dependent via `occupies(pos, t)`
	"""

	def __init__(self, width: int, height: int, default_cost: int = 1) -> None:
		if width <= 0 or height <= 0:
			raise ValueError("Grid dimensions must be positive")
		if default_cost < 1:
			raise ValueError("default_cost must be >= 1")
		self.bounds = Bounds(width, height)
		self._terrain: List[List[int]] = [
			[default_cost for _ in range(width)] for _ in range(height)
		]
		self._static_blocked: Set[Position] = set()
		self._dynamic_obstacles: List["DynamicObstacle"] = []

	@property
	def width(self) -> int:
		return self.bounds.width

	@property
	def height(self) -> int:
		return self.bounds.height

	def set_cost(self, pos: Position, cost: int) -> None:
		if cost < 1:
			raise ValueError("Cell cost must be >= 1")
		if not self.bounds.in_bounds(pos):
			raise ValueError("Position out of bounds")
		x, y = pos
		self._terrain[y][x] = cost

	def get_cost(self, pos: Position) -> int:
		if not self.bounds.in_bounds(pos):
			raise ValueError("Position out of bounds")
		x, y = pos
		return self._terrain[y][x]

	def set_static_obstacles(self, obstacles: Iterable[Position]) -> None:
		for pos in obstacles:
			if not self.bounds.in_bounds(pos):
				raise ValueError(f"Static obstacle {pos} out of bounds")
		self._static_blocked = set(obstacles)

	def get_static_obstacles(self) -> Set[Position]:
		return set(self._static_blocked)

	def add_static_obstacle(self, pos: Position) -> None:
		if not self.bounds.in_bounds(pos):
			raise ValueError("Position out of bounds")
		self._static_blocked.add(pos)

	def remove_static_obstacle(self, pos: Position) -> None:
		self._static_blocked.discard(pos)

	def add_dynamic_obstacle(self, obstacle: "DynamicObstacle") -> None:
		self._dynamic_obstacles.append(obstacle)

	def is_static_blocked(self, pos: Position) -> bool:
		return pos in self._static_blocked

	def is_dynamic_blocked(self, pos: Position, t: int) -> bool:
		for obs in self._dynamic_obstacles:
			if obs.occupies(pos, t):
				return True
		return False

	def is_blocked(self, pos: Position, t: int) -> bool:
		return self.is_static_blocked(pos) or self.is_dynamic_blocked(pos, t)

	def neighbors(self, pos: Position, t_next: int) -> List[Position]:
		"""4-neighborhood; returns positions passable at time t_next."""
		x, y = pos
		candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
		result: List[Position] = []
		for nx, ny in candidates:
			if not self.bounds.in_bounds((nx, ny)):
				continue
			if not self.is_blocked((nx, ny), t_next):
				result.append((nx, ny))
		return result

	def render(self, agent: Optional[Position], goal: Optional[Position], t: int) -> str:
		"""Return a simple ASCII rendering of the grid at time t."""
		lines: List[str] = []
		for y in range(self.height):
			row_chars: List[str] = []
			for x in range(self.width):
				pos = (x, y)
				ch = "."
				if self.is_static_blocked(pos):
					ch = "#"
				elif self.is_dynamic_blocked(pos, t):
					ch = "X"
				else:
					cost = self.get_cost(pos)
					ch = str(min(cost, 9))
				if goal is not None and pos == goal:
					ch = "G"
				if agent is not None and pos == agent:
					ch = "A"
				row_chars.append(ch)
			lines.append("".join(row_chars))
		return "\n".join(lines)


class DynamicObstacle:
	"""Protocol-like base to avoid circular import at type-check time."""

	def occupies(self, pos: Position, t: int) -> bool:  # pragma: no cover - interface only
		raise NotImplementedError 