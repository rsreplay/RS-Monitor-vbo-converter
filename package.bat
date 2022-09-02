@echo off

rem Update the .ico from icon.svg
rem magick convert -background none img/icon.svg img/icon.png
rem magick convert -background none img/icon.png -define icon:auto-resize img/icon.ico

rem pyinstaller --onefile --name "RS2vbo" --icon icon.ico main.py
rem pyinstaller RS2vbo.spec -y --clean
pyinstaller RS2vbo.spec -y
cp config.default.json dist/