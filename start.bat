@echo off
title 留学助手演示系统
color 0A

echo ================= 启动后端服务 =================
REM 启动后端可执行文件（位于 dist/ 目录）
start "" "dist\app-assistant.exe"

echo ================= 启动前端静态服务器 =================
REM 进入 dist 目录，启动 Python 静态服务器（端口 8080）
cd dist
start cmd /k "python -m http.server 8080"

echo ================= 自动打开浏览器 =================
REM 等待 3 秒确保服务启动，再打开浏览器
ping -n 3 127.0.0.1 > nul
start http://localhost:8080

echo.
echo 系统已启动！
echo - 后端服务：http://localhost:5000 （控制台请勿关闭）
echo - 前端页面：http://localhost:8080 （浏览器自动打开）
echo 若浏览器未自动打开，手动访问 http://localhost:8080 即可。