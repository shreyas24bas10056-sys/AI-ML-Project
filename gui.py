from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
import random
from typing import List, Tuple, Optional

from delivery.grid import Grid, Position
from delivery.dynamic import MovingObstacle
from delivery.agent import DeliveryAgent, AgentConfig
from delivery import search as search_mod

CELL_SIZE = 28
PADDING = 10

MODE_SET_GOAL = "Set Goal"
MODE_SET_START = "Set Start"
MODE_TOGGLE_WALL = "Toggle Wall"


class SimulatorGUI:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("Autonomous Delivery Agent - Grid Visualizer")

		self.width_var = tk.IntVar(value=20)
		self.height_var = tk.IntVar(value=12)
		self.seed_var = tk.IntVar(value=7)
		self.algo_var = tk.StringVar(value="astar")
		self.speed_var = tk.IntVar(value=200)  # ms per step
		self.mode_var = tk.StringVar(value=MODE_SET_GOAL)
		self.show_path_var = tk.BooleanVar(value=True)

		self.grid: Optional[Grid] = None
		self.agent: Optional[DeliveryAgent] = None
		self.goal: Optional[Position] = None
		self.start: Optional[Position] = None
		self.running = False
		self.after_id: Optional[str] = None
		self._last_planned_path: List[Position] = []

		self._build_ui()
		self._new_world()

	def _build_ui(self) -> None:
		top = ttk.Frame(self.root)
		top.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

		# Size controls
		for label, var in [("Width", self.width_var), ("Height", self.height_var), ("Seed", self.seed_var)]:
			ttk.Label(top, text=label).pack(side=tk.LEFT)
			entry = ttk.Entry(top, textvariable=var, width=5)
			entry.pack(side=tk.LEFT, padx=(0, 12))

		# Algorithm dropdown
		ttk.Label(top, text="Algorithm").pack(side=tk.LEFT)
		algo_cb = ttk.Combobox(top, textvariable=self.algo_var, values=["bfs", "ucs", "astar"], state="readonly", width=8)
		algo_cb.pack(side=tk.LEFT, padx=(0, 12))

		# Speed
		ttk.Label(top, text="Speed ms").pack(side=tk.LEFT)
		speed_entry = ttk.Entry(top, textvariable=self.speed_var, width=6)
		speed_entry.pack(side=tk.LEFT, padx=(0, 12))

		# Mode
		ttk.Label(top, text="Mode").pack(side=tk.LEFT)
		mode_cb = ttk.Combobox(top, textvariable=self.mode_var, values=[MODE_SET_GOAL, MODE_SET_START, MODE_TOGGLE_WALL], state="readonly", width=12)
		mode_cb.pack(side=tk.LEFT, padx=(0, 12))

		# Buttons
		self.btn_new = ttk.Button(top, text="New World", command=self._on_new)
		self.btn_new.pack(side=tk.LEFT)
		self.btn_start = ttk.Button(top, text="Start", command=self._on_start)
		self.btn_start.pack(side=tk.LEFT, padx=(6, 0))
		self.btn_pause = ttk.Button(top, text="Pause", command=self._on_pause)
		self.btn_pause.pack(side=tk.LEFT, padx=(6, 0))
		self.btn_step = ttk.Button(top, text="Step", command=self._on_step)
		self.btn_step.pack(side=tk.LEFT, padx=(6, 0))
		self.btn_reset_agent = ttk.Button(top, text="Reset Agent", command=self._on_reset_agent)
		self.btn_reset_agent.pack(side=tk.LEFT, padx=(6, 0))

		# Path toggle
		ttk.Checkbutton(top, text="Show Path", variable=self.show_path_var, command=self._draw).pack(side=tk.LEFT, padx=(12, 0))

		# Canvas and right legend
		mid = ttk.Frame(self.root)
		mid.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

		self.canvas = tk.Canvas(mid, bg="#ffffff")
		self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
		self.canvas.bind("<Button-1>", self._on_canvas_click)

		legend = ttk.Frame(mid)
		legend.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
		self._build_legend(legend)

		report_frame = ttk.Frame(mid)
		report_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=8, pady=8)
		ttk.Label(report_frame, text="Run Report", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
		self.report_text = tk.Text(report_frame, width=36, height=28, wrap="word")
		self.report_text.pack(fill=tk.BOTH, expand=True)
		self.report_text.configure(state=tk.DISABLED)

		# Status bar
		self.status = ttk.Label(self.root, text="Ready", anchor=tk.W)
		self.status.pack(side=tk.BOTTOM, fill=tk.X)

	def _build_legend(self, parent: ttk.Frame) -> None:
		items = [
			("Start", "#2ecc71"),
			("Goal", "#3498db"),
			("Wall", "#000000"),
			("Dynamic", "#e74c3c"),
			("Agent", "#f1c40f"),
		]
		for name, color in items:
			row = ttk.Frame(parent)
			row.pack(anchor=tk.W, pady=2)
			c = tk.Canvas(row, width=20, height=20)
			c.pack(side=tk.LEFT)
			c.create_rectangle(2, 2, 18, 18, fill=color, outline="#777")
			ttk.Label(row, text=name).pack(side=tk.LEFT, padx=6)
			ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)

	def _on_new(self) -> None:
		self._pause_loop()
		self._new_world()

	def _on_start(self) -> None:
		if self.agent is None:
			return
		self.running = True
		self._schedule_step()

	def _on_pause(self) -> None:
		self._pause_loop()

	def _on_step(self) -> None:
		self._pause_loop()
		self._do_step()

	def _on_reset_agent(self) -> None:
		if self.grid is None or self.start is None or self.goal is None:
			return
		self.agent = DeliveryAgent(self.grid, self.start, self.goal, AgentConfig(algo=self.algo_var.get(), random_seed=int(self.seed_var.get())))
		self.agent.plan()
		self._last_planned_path = self.agent.planned_path()
		self._draw()

	def _pause_loop(self) -> None:
		self.running = False
		if self.after_id is not None:
			try:
				self.root.after_cancel(self.after_id)
			except Exception:
				pass
			self.after_id = None

	def _schedule_step(self) -> None:
		if not self.running:
			return
		delay = max(10, int(self.speed_var.get()))
		self.after_id = self.root.after(delay, self._tick)

	def _tick(self) -> None:
		self._do_step()
		self._schedule_step()

	def _do_step(self) -> None:
		if self.agent is None or self.grid is None or self.goal is None:
			return
		if self.agent.at_goal():
			self._pause_loop()
			messagebox.showinfo("Done", "Agent reached goal!")
			return
		ok = self.agent.step()
		if not self.agent.planned_path():
			self.agent.plan()
		self._last_planned_path = self.agent.planned_path()
		self._draw()
		if not ok:
			self._pause_loop()
			messagebox.showwarning("Stuck", "Agent got stuck (no feasible move).")

	def _new_world(self) -> None:
		width = max(4, int(self.width_var.get()))
		height = max(4, int(self.height_var.get()))
		seed = int(self.seed_var.get())
		random.seed(seed)

		self.grid = Grid(width, height, default_cost=1)
		# Random terrain costs 1..5
		for y in range(height):
			for x in range(width):
				self.grid.set_cost((x, y), random.randint(1, 5))
		# Static obstacles ~10%
		static: List[Position] = []
		for y in range(height):
			for x in range(width):
				if random.random() < 0.10:
					static.append((x, y))
		self.grid.set_static_obstacles(static)
		# Dynamic obstacles: a few patrols
		num_dyn = max(1, (width * height) // 60)
		for i in range(num_dyn):
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
			self.grid.add_dynamic_obstacle(MovingObstacle(path=path, cycle=True))

		self.start = (0, 0)
		self.goal = (width - 1, height - 1)
		# Ensure start/goal valid
		if self.grid.is_static_blocked(self.start):
			self.grid.remove_static_obstacle(self.start)
		if self.grid.is_static_blocked(self.goal):
			self.grid.remove_static_obstacle(self.goal)
		self.grid.set_cost(self.start, max(1, self.grid.get_cost(self.start)))
		self.grid.set_cost(self.goal, max(1, self.grid.get_cost(self.goal)))

		algo = self.algo_var.get()
		self.agent = DeliveryAgent(self.grid, self.start, self.goal, AgentConfig(algo=algo, random_seed=seed))
		self.agent.plan()
		self._last_planned_path = self.agent.planned_path()
		self._resize_canvas()
		self._draw()

	def _resize_canvas(self) -> None:
		if self.grid is None:
			return
		w = self.grid.width * CELL_SIZE + 2 * PADDING
		h = self.grid.height * CELL_SIZE + 2 * PADDING
		self.canvas.config(width=w, height=h, scrollregion=(0, 0, w, h))

	def _color_for_cell(self, x: int, y: int) -> str:
		assert self.grid is not None
		pos = (x, y)
		if self.grid.is_static_blocked(pos):
			return "#000000"  # black walls
		# Shade by cost: lighter for low cost, darker for high cost
		cost = self.grid.get_cost(pos)
		base = max(30, 240 - (cost - 1) * 40)
		return f"#{base:02x}{base:02x}{base:02x}"

	def _draw(self) -> None:
		self.canvas.delete("all")
		if self.grid is None:
			return
		# Draw grid cells
		for y in range(self.grid.height):
			for x in range(self.grid.width):
				x0 = PADDING + x * CELL_SIZE
				y0 = PADDING + y * CELL_SIZE
				x1 = x0 + CELL_SIZE
				y1 = y0 + CELL_SIZE
				fill = self._color_for_cell(x, y)
				self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#d0d0d0")
				# draw terrain cost number
				self.canvas.create_text((x0 + x1)//2, (y0 + y1)//2, text=str(self.grid.get_cost((x, y))), fill="#666", font=("Segoe UI", 8))
		# Dynamic obstacles at current t
		if self.agent is not None:
			t = self.agent.t
			for y in range(self.grid.height):
				for x in range(self.grid.width):
					if self.grid.is_dynamic_blocked((x, y), t):
						x0 = PADDING + x * CELL_SIZE
						y0 = PADDING + y * CELL_SIZE
						x1 = x0 + CELL_SIZE
						y1 = y0 + CELL_SIZE
						self.canvas.create_rectangle(x0, y0, x1, y1, fill="#e74c3c", outline="#c0392b")
						self.canvas.create_text((x0 + x1)//2, (y0 + y1)//2, text="X", fill="white", font=("Segoe UI", 9, "bold"))
		# Path overlay
		if self.show_path_var.get() and self._last_planned_path:
			for i in range(1, len(self._last_planned_path)):
				x0, y0 = self._last_planned_path[i - 1]
				x1, y1 = self._last_planned_path[i]
				x0p = PADDING + x0 * CELL_SIZE + CELL_SIZE // 2
				y0p = PADDING + y0 * CELL_SIZE + CELL_SIZE // 2
				x1p = PADDING + x1 * CELL_SIZE + CELL_SIZE // 2
				y1p = PADDING + y1 * CELL_SIZE + CELL_SIZE // 2
				self.canvas.create_line(x0p, y0p, x1p, y1p, fill="#8e44ad", width=3)
		# Goal
		if self.goal is not None:
			xg, yg = self.goal
			x0 = PADDING + xg * CELL_SIZE
			y0 = PADDING + yg * CELL_SIZE
			x1 = x0 + CELL_SIZE
			y1 = y0 + CELL_SIZE
			self.canvas.create_rectangle(x0, y0, x1, y1, fill="#3498db", outline="#1f5f85")
			self.canvas.create_text((x0 + x1)//2, (y0 + y1)//2, text="G", fill="white", font=("Segoe UI", 10, "bold"))
		# Start
		if self.start is not None:
			xs, ys = self.start
			x0 = PADDING + xs * CELL_SIZE
			y0 = PADDING + ys * CELL_SIZE
			x1 = x0 + CELL_SIZE
			y1 = y0 + CELL_SIZE
			self.canvas.create_rectangle(x0, y0, x1, y1, outline="#2ecc71", width=3)
			self.canvas.create_text((x0 + x1)//2, (y0 + y1)//2, text="S", fill="#2ecc71", font=("Segoe UI", 10, "bold"))
		# Agent
		if self.agent is not None:
			xa, ya = self.agent.pos
			x0 = PADDING + xa * CELL_SIZE
			y0 = PADDING + ya * CELL_SIZE
			x1 = x0 + CELL_SIZE
			y1 = y0 + CELL_SIZE
			self.canvas.create_oval(x0 + 4, y0 + 4, x1 - 4, y1 - 4, fill="#f1c40f", outline="#8a7408")
			self.canvas.create_text(x0 + 8, y0 + 10, text=str(self.agent.t), fill="#333", font=("Segoe UI", 8))

		# Status text
		if self.agent is not None:
			self.status.config(text=f"t={self.agent.t} pos={self.agent.pos} goal={self.goal} mode={self.mode_var.get()} algo={self.algo_var.get()}")
			self._update_report()

	def _update_report(self) -> None:
		if self.agent is None:
			return
		report_lines: List[str] = []
		report_lines.append(f"Algorithm: {self.algo_var.get()}")
		report_lines.append(f"Time: {self.agent.t}")
		report_lines.append(f"Steps: {self.agent.steps_taken}")
		report_lines.append(f"Total Cost: {self.agent.total_cost}")
		report_lines.append(f"Replans: {self.agent.replan_count}")
		report_lines.append(f"Dynamic Conflicts: {self.agent.dynamic_conflicts}")
		report_lines.append(f"Last Action: {self.agent.last_action} (+{self.agent.last_step_cost})")
		report_lines.append(f"Reason: {self.agent.last_reason}")
		report_lines.append("")
		report_lines.append("Path Trace (t: (x,y)):")
		for t, pos in self.agent.path_trace[-200:]:
			report_lines.append(f"t={t}: {pos}")
		text = "\n".join(report_lines)
		self.report_text.configure(state=tk.NORMAL)
		self.report_text.delete("1.0", tk.END)
		self.report_text.insert(tk.END, text)
		self.report_text.configure(state=tk.DISABLED)

	def _on_canvas_click(self, event: tk.Event) -> None:
		if self.grid is None:
			return
		x = (event.x - PADDING) // CELL_SIZE
		y = (event.y - PADDING) // CELL_SIZE
		if x < 0 or y < 0 or x >= self.grid.width or y >= self.grid.height:
			return
		pos = (x, y)
		mode = self.mode_var.get()
		if mode == MODE_SET_GOAL:
			if not self.grid.is_static_blocked(pos):
				self.goal = pos
				if self.agent is not None:
					self.agent.goal = pos
					self.agent._plan = []
					self.agent.plan()
		elif mode == MODE_SET_START:
			if not self.grid.is_static_blocked(pos):
				self.start = pos
				if self.agent is not None and self.goal is not None:
					self.agent = DeliveryAgent(self.grid, self.start, self.goal, AgentConfig(algo=self.algo_var.get(), random_seed=int(self.seed_var.get())))
					self.agent.plan()
		elif mode == MODE_TOGGLE_WALL:
			if self.grid.is_static_blocked(pos):
				self.grid.remove_static_obstacle(pos)
			else:
				# Avoid placing wall on start/goal
				if pos != self.start and pos != self.goal:
					self.grid.add_static_obstacle(pos)
		self._last_planned_path = self.agent.planned_path() if self.agent is not None else []
		self._draw()


def main() -> None:
	root = tk.Tk()
	SimulatorGUI(root)
	root.mainloop()


if __name__ == "__main__":
	main() 