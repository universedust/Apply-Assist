@echo off
title 留学助手演示系统
color 0A

echo ================= 启动后端服务 =================
REM 启动后端可执行文件（位于 dist/ 目录）
start "" "dist\app-assistant.exe"

echo ================= 检查并释放端口 8080 =================
REM 检查端口 8080 是否被占用
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
    echo 发现端口 8080 被进程 %%a 占用
    taskkill /f /pid %%a
    echo 已终止进程 %%a
)

echo ================= 启动前端静态服务器 =================
REM 使用增强日志的 PowerShell 服务器
cd dist
start cmd /k powershell -ExecutionPolicy Bypass -Command "$listener = New-Object System.Net.HttpListener; $listener.Prefixes.Add('http://localhost:8080/'); try { $listener.Start(); Write-Host '静态服务器已启动：http://localhost:8080'; while ($true) { try { $context = $listener.GetContext(); $request = $context.Request; $response = $context.Response; $path = $request.Url.LocalPath; $method = $request.HttpMethod; $time = Get-Date -Format 'HH:mm:ss'; Write-Host ('[{0}] {1} {2}' -f $time, $method, $path); if ($path -eq '/') { $path = '/index.html' }; if ($path) { $filePath = [System.IO.Path]::Combine($(Get-Location).Path, $path.Substring(1)); if (Test-Path $filePath) { $content = [System.IO.File]::ReadAllBytes($filePath); $response.ContentType = if ($filePath.EndsWith('.html')) { 'text/html' } elseif ($filePath.EndsWith('.js')) { 'application/javascript' } elseif ($filePath.EndsWith('.css')) { 'text/css' } else { 'application/octet-stream' }; $response.ContentLength64 = $content.Length; $response.OutputStream.Write($content, 0, $content.Length); Write-Host ('  -> 200 OK ({0} bytes)' -f $content.Length); } else { $response.StatusCode = 404; Write-Host '  -> 404 Not Found'; } } else { $response.StatusCode = 400; Write-Host '  -> 400 Bad Request'; } $response.Close(); } catch { Write-Host ('  -> Error: {0}' -f $_); } } } catch { Write-Host '服务器启动错误:' $_; Write-Host '按任意键退出...'; $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown'); } finally { if ($listener.IsListening) { $listener.Stop(); } }"

echo ================= 自动打开浏览器 =================
REM 等待 3 秒确保服务启动，再打开浏览器
ping -n 3 127.0.0.1 > nul
start http://localhost:8080

echo.
echo 系统已启动！
echo - 后端服务：http://localhost:5000 （控制台请勿关闭）
echo - 前端页面：http://localhost:8080 （浏览器自动打开）
echo 若浏览器未自动打开，手动访问 http://localhost:8080 即可。