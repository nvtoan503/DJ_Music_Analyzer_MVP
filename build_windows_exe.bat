@echo off
setlocal
cd /d "%~dp0"
title DJ Music Analyzer - Build Windows EXE
where py >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Khong tim thay Python launcher. Hay cai Python 3.12 64-bit tu python.org.
  pause
  exit /b 1
)
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Can Python 3.12 64-bit. Hay cai tu python.org.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Tao moi truong Python...
  py -3.12 -m venv .venv
  if errorlevel 1 goto :failed
)
echo [2/4] Cai thu vien phu thuoc...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :failed
echo [3/4] Dong goi EXE...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --onedir --name DJMusicAnalyzer --collect-all librosa --collect-all soundfile --collect-all audioread main.py
if errorlevel 1 goto :failed
echo [4/4] Hoan thanh!
echo Mo app tai: dist\DJMusicAnalyzer\DJMusicAnalyzer.exe
echo LUU Y: Hay giu nguyen ca thu muc DJMusicAnalyzer, khong chi copy rieng EXE.
pause
exit /b 0
:failed
echo [ERROR] Dong goi that bai. Xem thong bao loi phia tren.
pause
exit /b 1
