@echo off
title MU Fireworks Simulator
cd /d "%~dp0"
py mu_updater.py
if errorlevel 1 (
    echo.
    echo The updater could not complete. You can still launch the installed game.
    pause
)
py mu_fireworks.py
