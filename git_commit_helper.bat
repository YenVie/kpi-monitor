@echo off
REM ========================================
REM    GIT COMMIT HELPER - Trợ lý Git
REM ========================================
REM Script này giúp bạn commit code dễ dàng hơn
REM Nhưng bạn vẫn phải tự quyết định khi nào commit!

echo.
echo ========================================
echo    🔍 KIỂM TRA THAY ĐỔI
echo ========================================
echo.
git status
echo.
echo ========================================
echo.

REM Kiểm tra xem có thay đổi không
git diff --quiet
if %errorlevel% == 0 (
    git diff --cached --quiet
    if %errorlevel% == 0 (
        echo ✅ Không có thay đổi nào!
        echo.
        pause
        exit /b
    )
)

echo Bạn có muốn xem chi tiết thay đổi không? (Y/N)
set /p view_diff=
if /i "%view_diff%"=="Y" (
    echo.
    echo ========================================
    echo    📝 CHI TIẾT THAY ĐỔI
    echo ========================================
    git diff
    echo.
    echo ========================================
    echo.
)

echo.
echo ========================================
echo    💾 COMMIT THAY ĐỔI
echo ========================================
echo.
echo Bạn muốn commit thay đổi không? (Y/N)
set /p confirm=
if /i "%confirm%"=="Y" (
    echo.
    echo 📝 Nhập message commit (mô tả thay đổi):
    echo    Ví dụ: "Fix bug: Sửa lỗi fuzzy matching"
    echo.
    set /p message=
    
    if "%message%"=="" (
        echo.
        echo ❌ Message không được để trống!
        echo 💡 Ví dụ message tốt:
        echo    - "Thêm tính năng phân tích theo ngày"
        echo    - "Fix bug: Sửa lỗi crash khi file rỗng"
        echo    - "Cải thiện performance khi load file lớn"
        echo.
        pause
        exit /b
    )
    
    echo.
    echo ⏳ Đang thêm file vào staging...
    git add .
    
    echo ⏳ Đang commit...
    git commit -m "%message%"
    
    if %errorlevel% == 0 (
        echo.
        echo ✅ Đã commit thành công!
        echo.
        echo ========================================
        echo    📜 LỊCH SỬ COMMIT
        echo ========================================
        git log --oneline -3
        echo.
    ) else (
        echo.
        echo ❌ Có lỗi xảy ra khi commit!
        echo.
    )
) else (
    echo.
    echo ❌ Hủy commit. Thay đổi vẫn còn trong file.
    echo 💡 Nhớ commit sau khi sửa code xong!
    echo.
)

pause

