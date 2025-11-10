@echo off
chcp 65001 >nul
cd /d "%~dp0"
git add app.py requirements.txt .gitignore README.md *.py
git commit -m "Update code"
git push origin main
if %errorlevel% neq 0 (
    git pull origin main --no-rebase
    git push origin main
)
echo Done!

