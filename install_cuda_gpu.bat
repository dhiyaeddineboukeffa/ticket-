@echo off
setlocal
cd /d "%~dp0"
title Installing CUDA Acceleration for NVIDIA GeForce GTX 1070

echo ============================================================
echo Installing CUDA Acceleration for NVIDIA GeForce GTX 1070
echo ============================================================
echo.

set "WHEEL=torch-2.5.1+cu121-cp311-cp311-win_amd64.whl"
set "URL=https://download.pytorch.org/whl/cu121/%WHEEL%"

echo Step 1/3: Clearing any corrupted pip cache...
call .venv\Scripts\python.exe -m pip cache purge

echo.
echo Step 2/3: Downloading PyTorch CUDA wheel with auto-resume...
echo (If network drops, re-running this script resumes where it left off!)
curl.exe -C - --retry 20 --retry-delay 3 --retry-all-errors -L -o "%WHEEL%" "%URL%"

if errorlevel 1 (
    echo.
    echo [ERROR] Download was interrupted. Simply double-click install_cuda_gpu.bat again to resume.
    pause
    exit /b 1
)

echo.
echo Step 3/3: Installing PyTorch & Torchvision into .venv...
call .venv\Scripts\activate.bat
python -m pip install "%WHEEL%" torchvision --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir

if exist "%WHEEL%" (
    echo.
    echo Cleaning up installer package to free disk space...
    del "%WHEEL%"
)

echo.
echo ============================================================
echo Verifying CUDA Hardware Acceleration:
echo ============================================================
python -c "import torch; print('CUDA Enabled:', torch.cuda.is_available()); print('Active Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU only')"

echo.
echo Setup finished! You can now launch run.bat to use your GTX 1070!
pause
