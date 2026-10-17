@echo off
echo ============================================================
echo Installing CUDA Acceleration for NVIDIA GeForce GTX 1070
echo ============================================================
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Starting download (approx 2.4 GB, please keep window open)...
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --default-timeout 1000 --force-reinstall
echo.
python -c "import torch; print('CUDA Enabled:', torch.cuda.is_available()); print('Active Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU only')"
echo.
echo Setup finished! Press any key to exit.
pause
