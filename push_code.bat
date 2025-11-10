@echo off
chcp 65001 >nul
echo ========================================
echo    PUSH CODE LÊN GITHUB
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Đang kiểm tra thay đổi...
git status --short
echo.

echo [2/4] Đang thêm file vào staging...
git add app.py requirements.txt .gitignore README.md *.py
if %errorlevel% neq 0 (
    echo Lỗi: Không thể add file!
    pause
    exit /b 1
)
echo ✓ Đã thêm file thành công!
echo.

echo [3/4] Đang commit...
set /p commit_msg="Nhập message cho commit (hoặc Enter để dùng message mặc định): "
if "%commit_msg%"=="" set commit_msg=Update code
git commit -m "%commit_msg%"
if %errorlevel% neq 0 (
    echo Lỗi: Không thể commit!
    pause
    exit /b 1
)
echo ✓ Đã commit thành công!
echo.

echo [4/4] Đang push lên GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo.
    echo ⚠ Lỗi khi push! Có thể cần pull trước.
    echo Đang thử pull...
    git pull origin main --no-rebase
    if %errorlevel% neq 0 (
        echo Lỗi: Không thể pull!
        pause
        exit /b 1
    )
    echo Đang push lại...
    git push origin main
    if %errorlevel% neq 0 (
        echo Lỗi: Không thể push!
        pause
        exit /b 1
    )
)
echo.
echo ========================================
echo    ✓ HOÀN TẤT! Đã push code lên GitHub
echo ========================================
echo.
pause

