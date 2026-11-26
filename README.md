# MU Fireworks Simulator

A visual-only 2D fireworks show simulator built with Python and Pygame-ce.

## v0.2.0 — Grand Show

- Eight selectable shell styles: Peony, Chrysanthemum, Willow, Ring, Palm, Crackle, Strobe, and Brocade
- Randomized burst geometry, colors, particle speeds, spark lifetimes, and glitter
- Crackle-style splitting sparks and secondary glitter rain
- Smoke clouds, bright cores, rocket trails, and additive glow
- Improved backyard skyline, night gradient, and twinkling stars
- Automatic show mode, pause, simulation speed, fullscreen, and HUD toggle

## Requirements

- Python 3
- Pygame-ce

Install Pygame-ce:

```powershell
py -m pip install pygame-ce
```

## Install

Download these files into the same folder:

- `mu_fireworks.py`
- `mu_updater.py`
- `version.json`
- `Run MU Fireworks.bat`

Double-click **Run MU Fireworks.bat**. It checks GitHub for updates, asks before installing, then starts the simulator.

You can also run the updater manually with `py mu_updater.py`, or launch the game directly with `py mu_fireworks.py`.

The updater validates Python syntax and creates a timestamped backup before replacing the game file.

## Controls

| Key / Input | Action |
|---|---|
| Left click | Launch toward cursor |
| Space | Launch random shell |
| 1–8 | Select a firework style |
| 0 | Random style |
| B | Toggle black sky / backyard |
| R | Toggle automatic show |
| P | Pause / resume |
| + / - | Adjust simulation speed |
| H | Toggle HUD |
| F | Toggle fullscreen |
| C | Clear sky |
| Esc | Quit |

This project is a visual particle simulation only. It does not provide real-world firework construction or launch instructions.
