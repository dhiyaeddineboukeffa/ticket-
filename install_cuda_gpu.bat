@echo off
cd /d "%~dp0"
title Installing CUDA Acceleration for NVIDIA GeForce GTX 1070
call .venv\Scripts\python.exe install_cuda.py
pause
