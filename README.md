# MU Fireworks Simulator

A visual-only 2D fireworks particle simulator built with Python and Pygame-ce.

## Requirements

- Python 3
- Pygame-ce

Install Pygame-ce:

```powershell
py -m pip install pygame-ce
```

## Install

Download these files from the repository and put them in the same folder:

- `mu_fireworks.py`
- `mu_updater.py`
- `version.json`
- `Run MU Fireworks.bat`

Then double-click **Run MU Fireworks.bat**. It checks GitHub for an update, asks before installing, and then starts the simulator.

You can also run the updater manually:

```powershell
py mu_updater.py
```

Or launch the game without checking for updates:

```powershell
py mu_fireworks.py
```

## Updating

The updater reads `version.json` from the repository's `main` branch. When a newer version is available, it asks before downloading. It validates the Python syntax and creates a timestamped backup of the existing `mu_fireworks.py` before replacing it.

## Controls

- Left click: launch a virtual bottle-rocket effect
- Space: launch a random virtual firework
- B: toggle black sky / backyard
- R: toggle automatic random launches
- C: clear particles
- Esc: quit

This project is a visual particle simulation only. It does not provide real-world firework construction or launch instructions.
