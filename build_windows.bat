@echo off
echo Building BetterDisplay PC Server...
pip install -r server\requirements.txt
pip install pyinstaller

cd server
pyinstaller --noconfirm --noconsole --onefile --windowed --icon=..\assets\icon.jpg --add-data=..\assets\icon.jpg;assets main.py

echo Build complete! The executable is located in server\dist\main.exe
pause
