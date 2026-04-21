@echo off
chcp 65001 >nul
echo ========================================
echo   社区物业管理系统 - 打包为可执行文件
echo ========================================
echo.

call conda activate gauss

echo.
echo 开始打包...
pyinstaller -w -F --name "社区物业管理系统" main.py

echo.
if exist "dist\社区物业管理系统.exe" (
    echo 打包成功！可执行文件位于: dist\社区物业管理系统.exe
) else (
    echo 打包失败，请检查错误信息。
)
pause
