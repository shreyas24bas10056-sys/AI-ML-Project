# Autonomous Delivery Agent (2D Grid) 
  
A Python-based autonomous delivery agent that navigates a 2D grid city with terrain costs, static obstacles, and dynamic moving obstacles. Includes BFS, UCS, and A* pathfinding plus a hill-climbing-based replanning strategy. 
  
## Features  
  
- **Multiple Search Algorithms**: BFS, UCS, and A* with Manhattan distance heuristic  
- **Dynamic Obstacle Avoidance**: Agent replans when moving obstacles block its path  
- **Interactive GUI**: Visual grid with real-time agent movement and path tracking  
- **Terrain Costs**: Different movement costs for different terrain types  
- **Hill-Climbing Replanning**: Local search fallback when global replanning fails  
- **Live Metrics**: Real-time tracking of path cost, replans, and conflicts 
  
## Requirements  
  
- Python 3.9 or higher  
- No external dependencies (uses only Python standard library)  
- Tkinter (usually included with Python) 
  
## Installation  
  
1. Clone or download this repository  
2. Navigate to the project directory  
3. No additional installation required 
  
## Usage  
  
### GUI Mode (Recommended)  
  
Run the interactive GUI:  
  
```bash  
python gui.py  
``` 
  
#### GUI Controls  
  
- **Width/Height**: Set grid dimensions  
- **Seed**: Random seed for reproducible results  
- **Algorithm**: Choose BFS, UCS, or A*  
- **Speed**: Animation speed in milliseconds  
- **Mode**: Set Goal, Set Start, or Toggle Wall  
- **New World**: Generate new random grid  
- **Start/Pause/Step**: Control simulation  
- **Reset Agent**: Reset agent to start position  
- **Show Path**: Toggle path visualization 
  
### CLI Mode  
  
Run the command-line simulator:  
  
```bash  
python simulate.py --algo astar --width 20 --height 12 --seed 7  
``` 
  
#### CLI Options  
  
- `--algo`: Algorithm to use (bfs, ucs, astar)  
- `--width`: Grid width (default: 20)  
- `--height`: Grid height (default: 12)  
- `--seed`: Random seed (default: 7)  
- `--steps`: Max simulation steps (default: 400)  
- `--print-every`: Print frequency (default: 1) 
  
## Project Structure  
  
```  
aiml/  
ÃÄÄ delivery/  
³   ÃÄÄ __init__.py  
³   ÃÄÄ grid.py          # Grid model with terrain costs and obstacles  
³   ÃÄÄ dynamic.py       # Dynamic obstacle models  
³   ÃÄÄ search.py        # BFS, UCS, A* algorithms  
³   ÀÄÄ agent.py         # Delivery agent with replanning  
ÃÄÄ gui.py              # Interactive GUI  
ÃÄÄ simulate.py         # CLI simulator  
ÃÄÄ experiments.py      # Benchmarking script  
ÃÄÄ requirements.txt    # Dependencies  
ÀÄÄ README.md          # This file  
``` 
  
## How It Works  
  
### Environment Model  
  
- **Grid**: 2D grid with integer terrain costs (1-5)  
- **Static Obstacles**: Impassable walls (black cells)  
- **Dynamic Obstacles**: Moving red X cells that follow patrol paths  
- **Start/Goal**: Agent starts at (0,0), goal at (width-1, height-1) 
  
### Search Algorithms  
  
- **BFS**: Breadth-first search, minimizes steps  
- **UCS**: Uniform-cost search, minimizes path cost  
- **A***: A* with Manhattan distance heuristic  
  
### Replanning Strategy  
  
- **Dynamic Obstacle Detection**: Agent checks for conflicts at each step  
- **Full Replanning**: When blocked, agent replans from current position  
- **Hill-Climbing Fallback**: Local search when global replanning fails 
  
- **Dynamic Obstacle Detection**: Agent checks for conflicts at each step  
- **Full Replanning**: When blocked, agent replans from current position  
- **Hill-Climbing Fallback**: Local search when global replanning fails 
  
## Examples  
  
### Basic Usage  
  
Run GUI with default settings:  
  
```bash  
python gui.py  
``` 
  
### CLI Examples  
  
Run A* on a 30x20 grid:  
  
```bash  
python simulate.py --algo astar --width 30 --height 20 --seed 42  
``` 
  
Run BFS with custom settings:  
  
```bash  
python simulate.py --algo bfs --width 15 --height 10 --steps 200 --print-every 5  
``` 
  
## Grid Legend  
  
- **S**: Start position (green border)  
- **G**: Goal position (blue)  
- **A**: Agent (yellow circle with time)  
- **#**: Static wall (black)  
- **X**: Dynamic obstacle (red)  
- **Numbers**: Terrain cost (1-5, lighter = cheaper)  
- **Purple line**: Planned path 
  
## Troubleshooting  
  
### Common Issues  
  
**GUI doesn't open**:  
- Ensure you have a desktop environment  
- Check if Tkinter is installed: `python -c "import tkinter"`  
  
**Agent gets stuck**:  
- Try a different seed or algorithm  
- Increase max steps with `--steps` 
  
## Contributing  
  
1. Fork the repository  
2. Create a feature branch  
3. Make your changes  
4. Test thoroughly  
5. Submit a pull request 
  
## License  
  
This project is open source and available under the MIT License. 
  
---  
  
For more details, see the source code or run `python experiments.py` for performance benchmarks. 
