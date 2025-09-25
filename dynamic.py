from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

Position = Tuple[int, int]


@dataclass
class MovingObstacle:
	"""Obstacle that moves along a predefined path, cycling by default.

	If `cycle` is False and t exceeds path length, it stays at the last cell.
	"""
	path: Sequence[Position]
	cycle: bool = True

	def position_at(self, t: int) -> Position:
		if not self.path:
			raise ValueError("MovingObstacle requires a non-empty path")
		if t < 0:
			raise ValueError("t must be non-negative")
		if self.cycle:
			idx = t % len(self.path)
			return self.path[idx]
		else:
			idx = min(t, len(self.path) - 1)
			return self.path[idx]

	def occupies(self, pos: Position, t: int) -> bool:
		return self.position_at(t) == pos 