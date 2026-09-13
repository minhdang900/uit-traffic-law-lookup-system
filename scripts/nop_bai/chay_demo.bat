@echo off
REM Chay demo tu anh Docker da dong goi -- Windows.
REM Nhay doi vao tep nay la xong. Khong can cai Python.
REM
REM   chay_demo.bat        -> mo tai http://localhost:8000
REM   chay_demo.bat dung   -> dung va don container
setlocal
set ANH=traffic-law:latest
set TEN=traffic-law-demo
if "%PORT%"=="" set PORT=8000

if "%1"=="dung" (
  docker rm -f %TEN% >nul 2>&1
  echo Da dung va don container %TEN%.
  goto :eof
)

docker info >nul 2>&1
if errorlevel 1 (
  echo Docker chua chay. Hay mo Docker Desktop roi thu lai.
  pause
  exit /b 1
)

docker image inspect %ANH% >nul 2>&1
if errorlevel 1 (
  echo ==^> Nap anh Docker ^(mat 30-60 giay^)...
  docker load -i "%~dp0traffic-law-image.tar.gz"
) else (
  echo ==^> Da co anh %ANH%, bo qua buoc nap.
)

docker rm -f %TEN% >nul 2>&1
echo ==^> Khoi dong tren cong %PORT%...
docker run -d --name %TEN% -p %PORT%:8000 %ANH% >nul

echo ==^> Dang nap co so tri thuc, doi khoang 30 giay...
timeout /t 30 /nobreak >nul

echo.
echo   SAN SANG:  http://localhost:%PORT%
echo.
echo   /            Tra cuu
echo   /chi-so      Chi so danh gia
echo   /chu-de      Duyet chu de
echo   /hieu-luc    Hieu luc theo thoi gian
echo   /api/docs    Tai lieu API
echo.
echo   Dung lai:  chay_demo.bat dung
echo.
start "" "http://localhost:%PORT%"
endlocal
