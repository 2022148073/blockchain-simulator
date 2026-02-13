@echo off
echo ========================================
echo GitHub Push Script
echo ========================================
echo.

REM 사용자에게 GitHub 저장소 URL 입력 요청
set /p REPO_URL="GitHub 저장소 URL을 입력하세요 (예: https://github.com/username/blockchain-simulator.git): "

echo.
echo 저장소 URL: %REPO_URL%
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM 원격 저장소 추가
echo [1/2] 원격 저장소 연결 중...
git remote add origin %REPO_URL%

REM 푸시
echo [2/2] GitHub에 업로드 중...
git push -u origin main

echo.
echo ========================================
echo 완료! GitHub에 업로드되었습니다.
echo ========================================
echo.
pause
