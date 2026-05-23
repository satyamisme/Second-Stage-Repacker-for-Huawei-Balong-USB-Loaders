@echo off
setlocal enabledelayedexpansion
title Balong USBLoader Patcher - Complete
color 0A

set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

set "BIN=%BASE%\bin"
set "WORK=%BASE%\work"
set "OUT=%BASE%\output"
set "LOG=%BASE%\patcher.log"

if not exist "%BIN%" mkdir "%BIN%"
if not exist "%WORK%" mkdir "%WORK%"
if not exist "%OUT%" mkdir "%OUT%"

:: Auto-detect loader
set "LOADER="
for %%F in ("%BASE%\*.bin") do (
    if not defined LOADER set "LOADER=%%F"
)

:: Set output filename
if defined LOADER (
    for %%X in ("%LOADER%") do set "LOADER_NAME=%%~nX"
    set "OUTFILE=%OUT%\%LOADER_NAME%_patched.bin"
) else (
    set "OUTFILE=%OUT%\usbloader_patched.bin"
)

:MENU
cls
echo.
echo ============================================================
echo        Balong USBLoader Patcher - Complete Edition
echo ============================================================
echo.
if defined LOADER (echo Loader: %LOADER%) else echo No loader .bin found
echo Output: %OUTFILE%
echo.
echo   STATUS:
if exist "%WORK%\usbloader.bin" (echo   [1] [OK] Source) else echo   [1] [  ] Source
if exist "%WORK%\usbldr_unpacked\metadata.txt" (echo   [2] [OK] Unpacked) else echo   [2] [  ] Unpacked
if exist "%WORK%\second_out\.extract_meta" (echo   [S] [OK] Second stage) else echo   [S] [  ] Not extracted
if exist "%WORK%\block1_patched.bin" (echo   [3] [OK] Repacked) else echo   [3] [  ] Not repacked
if exist "%OUTFILE%" (echo   [4] [OK] Final output) else echo   [4] [  ] Not built
echo.
echo ============================================================
echo MANUAL STEPS
echo ============================================================
echo   [1] Load source (auto-detect)
echo   [2] Load source (manual)
echo   [3] Unpack USBLoader
echo   [40] Extract second stage
echo   [41] Open second stage folder
echo   [42] Repack second stage
echo   [11] Build final output
echo   [34] Clean work folder
echo   [36] Exit
echo.
echo ============================================================
echo QUICK ACTIONS
echo ============================================================
echo   [80] Show loader info (without unpack)
echo   [81] Verify repack (compare original vs patched)
echo   [82] Make safe loader (disable flash erase)
echo   [83] Test all loaders in folder (batch mode)
echo.
echo ============================================================
echo AUTO WORKFLOWS
echo ============================================================
echo   [90] FULL: Unpack + Extract + Open + Wait + Repack + Build
echo   [91] FAST: Repack existing second stage + Build
echo   [92] PATCH: Add patchblocked.sh + Repack + Build
echo.
echo ============================================================
echo UTILITIES
echo ============================================================
echo   [95] Check files
echo   [96] Flash instructions
echo   [97] View log
echo.
set /p "C=Option: "

:: MANUAL STEPS
if "%C%"=="1" goto LOAD_AUTO
if "%C%"=="2" goto LOAD_MANUAL
if "%C%"=="3" goto UNPACK
if "%C%"=="40" goto EXTRACT_SECOND
if "%C%"=="41" goto OPEN_SECOND
if "%C%"=="42" goto REPACK_SECOND
if "%C%"=="11" goto BUILD_FINAL
if "%C%"=="34" goto CLEAN
if "%C%"=="36" exit /b

:: QUICK ACTIONS
if "%C%"=="80" goto SHOW_INFO
if "%C%"=="81" goto VERIFY_REPACK
if "%C%"=="82" goto MAKE_SAFE
if "%C%"=="83" goto TEST_ALL

:: AUTO WORKFLOWS
if "%C%"=="90" goto AUTO_FULL
if "%C%"=="91" goto AUTO_FAST
if "%C%"=="92" goto AUTO_PATCH

:: UTILITIES
if "%C%"=="95" goto CHECK
if "%C%"=="96" goto FLASH
if "%C%"=="97" goto VIEWLOG

goto MENU

:: ==================== MANUAL STEPS ====================

:LOAD_AUTO
if not defined LOADER (
    echo No .bin file found
    pause
    goto MENU
)
for %%X in ("%LOADER%") do set "LOADER_NAME=%%~nX"
set "OUTFILE=%OUT%\%LOADER_NAME%_patched.bin"
copy /Y "%LOADER%" "%WORK%\usbloader.bin" >nul 2>&1
echo Loaded: %LOADER%
echo Output: %OUTFILE%
pause
goto MENU

:LOAD_MANUAL
set "F="
set /p "F=Enter full path to .bin: "
if not defined F goto MENU
if not exist "%F%" (
    echo File not found
    pause
    goto MENU
)
for %%X in ("%F%") do set "LOADER_NAME=%%~nX"
set "OUTFILE=%OUT%\%LOADER_NAME%_patched.bin"
copy /Y "%F%" "%WORK%\usbloader.bin" >nul 2>&1
echo Loaded: %F%
pause
goto MENU

:UNPACK
if not exist "%WORK%\usbloader.bin" (
    echo Load source first (option 1 or 2)
    pause
    goto MENU
)
if exist "%WORK%\usbldr_unpacked\metadata.txt" (
    echo Already unpacked
    pause
    goto MENU
)
echo.
echo ==========================================
echo UNPACKING USBLOADER
echo ==========================================
python "%BIN%\usbloader_packer.py" -u "%WORK%\usbloader.bin" -d "%WORK%\usbldr_unpacked"
if errorlevel 1 (
    echo FAILED
    pause
    goto MENU
)
copy /Y "%WORK%\usbldr_unpacked\block1_usbldr.bin" "%WORK%\block1_usbldr.bin" >nul 2>&1
echo Unpack complete
pause
goto MENU

:EXTRACT_SECOND
if not exist "%WORK%\block1_usbldr.bin" (
    echo Unpack first (option 3)
    pause
    goto MENU
)
if exist "%WORK%\second_out\.extract_meta" (
    echo Already extracted
    pause
    goto MENU
)
echo.
echo ==========================================
echo EXTRACTING SECOND STAGE
echo ==========================================
python "%BIN%\extract_second.py" --bin "%WORK%\block1_usbldr.bin" --out "%WORK%\second_out"
if errorlevel 1 (
    echo FAILED
    pause
    goto MENU
)
echo Extracted to work\second_out
pause
goto MENU

:OPEN_SECOND
if not exist "%WORK%\second_out" (
    echo Extract first (option 40)
    pause
    goto MENU
)
start explorer "%WORK%\second_out"
goto MENU

:REPACK_SECOND
if not exist "%WORK%\second_out" (
    echo Extract first (option 40)
    pause
    goto MENU
)
if not exist "%WORK%\block1_usbldr.bin" (
    echo Unpack first (option 3)
    pause
    goto MENU
)
echo.
echo ==========================================
echo REPACKING SECOND STAGE
echo ==========================================
python "%BIN%\repack_inject.py" --bin "%WORK%\block1_usbldr.bin" --out "%WORK%\block1_patched.bin" --second "%WORK%\second_out"
if errorlevel 1 (
    echo FAILED
    pause
    goto MENU
)
echo Repacked: work\block1_patched.bin
pause
goto MENU

:BUILD_FINAL
if not exist "%WORK%\block1_patched.bin" (
    echo Repack first (option 42)
    pause
    goto MENU
)
if not exist "%WORK%\usbldr_unpacked\metadata.txt" (
    echo Unpack first (option 3)
    pause
    goto MENU
)
copy /Y "%WORK%\block1_patched.bin" "%WORK%\usbldr_unpacked\block1_usbldr.bin" >nul 2>&1
echo.
echo ==========================================
echo BUILDING FINAL LOADER
echo ==========================================
python "%BIN%\usbloader_packer.py" -p "%WORK%\usbldr_unpacked" -o "%OUTFILE%"
if errorlevel 1 (
    echo FAILED
    pause
    goto MENU
)
echo.
echo ==========================================
echo FINAL OUTPUT: %OUTFILE%
echo ==========================================
pause
goto MENU

:: ==================== QUICK ACTIONS ====================

:SHOW_INFO
if not defined LOADER (
    echo No loader found
    pause
    goto MENU
)
echo.
echo ==========================================
echo LOADER INFO
echo ==========================================
python "%BIN%\usbloader_packer.py" --info "%LOADER%"
pause
goto MENU

:VERIFY_REPACK
if not defined LOADER (
    echo No original loader found
    pause
    goto MENU
)
if not exist "%OUTFILE%" (
    echo Repacked file not found. Build first (option 11)
    pause
    goto MENU
)
echo.
echo ==========================================
echo VERIFY REPACK
echo ==========================================
python "%BIN%\usbloader_packer.py" --verify "%LOADER%" "%OUTFILE%"
pause
goto MENU

:MAKE_SAFE
if not defined LOADER (
    echo No loader found
    pause
    goto MENU
)
if not exist "%OUT%" mkdir "%OUT%"
set "SAFE_OUT=%OUT%\%LOADER_NAME%_safe.bin"
echo.
echo ==========================================
echo CREATE SAFE LOADER
echo ==========================================
copy /Y "%LOADER%" "%SAFE_OUT%" >nul 2>&1
python "%BIN%\usbloader_packer.py" --safe "%SAFE_OUT%"
if errorlevel 1 (
    echo FAILED
    pause
    goto MENU
)
echo.
echo Safe loader saved to: %SAFE_OUT%
pause
goto MENU

:TEST_ALL
echo.
echo ==========================================
echo TESTING ALL LOADERS IN FOLDER
echo ==========================================
echo.
echo This test performs:
echo   1. Unpack USBLoader
echo   2. Extract second stage
echo   3. Repack second stage
echo   4. Build final loader
echo.
echo If all 4 steps pass, the loader is compatible.
echo.

set "TEST_COUNT=0"
set "PASS_COUNT=0"
set "FAIL_COUNT=0"

for %%F in ("%BASE%\*.bin") do (
    set /a TEST_COUNT+=1
    echo.
    echo ==========================================
    echo [TEST !TEST_COUNT!] %%~nxF
    echo ==========================================
    
    set "TEST_PASS=1"
    
    :: Clean temp folders
    if exist "temp_%%~nF" rd /s /q "temp_%%~nF" 2>nul
    mkdir "temp_%%~nF" 2>nul
    
    :: Step 1: Unpack
    echo.
    echo [1/4] Unpacking...
    python "%BIN%\usbloader_packer.py" -u "%%F" -d "temp_%%~nF" 2>&1
    if errorlevel 1 (
        echo   FAILED - Unpack error
        set "TEST_PASS=0"
    ) else (
        echo   OK - Unpack successful
    )
    
    :: Check block1 exists
    if "!TEST_PASS!"=="1" (
        if not exist "temp_%%~nF\block1_usbldr.bin" (
            echo   FAILED - block1_usbldr.bin not found
            set "TEST_PASS=0"
        )
    )
    
    :: Step 2: Extract second stage
    if "!TEST_PASS!"=="1" (
        echo.
        echo [2/4] Extracting second stage...
        python "%BIN%\extract_second.py" --bin "temp_%%~nF\block1_usbldr.bin" --out "temp_%%~nF_sec" 2>&1
        if errorlevel 1 (
            echo   FAILED - Extract error
            set "TEST_PASS=0"
        ) else (
            echo   OK - Extract successful
        )
    )
    
    :: Step 3: Repack second stage
    if "!TEST_PASS!"=="1" (
        echo.
        echo [3/4] Repacking second stage...
        python "%BIN%\repack_inject.py" --bin "temp_%%~nF\block1_usbldr.bin" --out "temp_%%~nF\block1_patched.bin" --second "temp_%%~nF_sec" 2>&1
        if errorlevel 1 (
            echo   FAILED - Repack error
            set "TEST_PASS=0"
        ) else (
            echo   OK - Repack successful
        )
    )
    
    :: Step 4: Build final loader
    if "!TEST_PASS!"=="1" (
        echo.
        echo [4/4] Building final loader...
        python "%BIN%\usbloader_packer.py" -p "temp_%%~nF" -o "test_output_%%~nF.bin" 2>&1
        if errorlevel 1 (
            echo   FAILED - Build error
            set "TEST_PASS=0"
        ) else (
            echo   OK - Build successful
            for %%A in ("%%F") do echo   Original size: %%~zA bytes
            for %%A in ("test_output_%%~nF.bin") do echo   Patched size: %%~zA bytes
        )
    )
    
    :: Result
    echo.
    if "!TEST_PASS!"=="1" (
        echo RESULT: PASSED
        set /a PASS_COUNT+=1
    ) else (
        echo RESULT: FAILED
        set /a FAIL_COUNT+=1
    )
    
    :: Cleanup
    if exist "temp_%%~nF" rd /s /q "temp_%%~nF" 2>nul
    if exist "temp_%%~nF_sec" rd /s /q "temp_%%~nF_sec" 2>nul
    if exist "test_output_%%~nF.bin" del /f /q "test_output_%%~nF.bin" 2>nul
)

echo.
echo ==========================================
echo TEST SUMMARY
echo ==========================================
echo Total loaders tested: %TEST_COUNT%
echo Passed: %PASS_COUNT%
echo Failed: %FAIL_COUNT%
echo.
if %FAIL_COUNT%==0 (
    echo All loaders are compatible!
) else (
    echo %FAIL_COUNT% loader(s) failed compatibility test.
)
echo.
echo Press any key to return to menu...
pause >nul
goto MENU

:: ==================== AUTO WORKFLOWS ====================

:AUTO_FULL
echo.
echo ==========================================
echo [90] FULL WORKFLOW
echo ==========================================

if not exist "%WORK%\usbloader.bin" (
    if not defined LOADER (
        echo No loader found
        pause
        goto MENU
    )
    for %%X in ("%LOADER%") do set "LOADER_NAME=%%~nX"
    set "OUTFILE=%OUT%\%LOADER_NAME%_patched.bin"
    copy /Y "%LOADER%" "%WORK%\usbloader.bin" >nul 2>&1
    echo Source loaded
)

if not exist "%WORK%\usbldr_unpacked\metadata.txt" (
    echo.
    echo --- UNPACKING ---
    python "%BIN%\usbloader_packer.py" -u "%WORK%\usbloader.bin" -d "%WORK%\usbldr_unpacked"
    if errorlevel 1 (
        echo Unpack FAILED
        pause
        goto MENU
    )
    copy /Y "%WORK%\usbldr_unpacked\block1_usbldr.bin" "%WORK%\block1_usbldr.bin" >nul 2>&1
    echo Unpack OK
)

if not exist "%WORK%\second_out\.extract_meta" (
    echo.
    echo --- EXTRACTING SECOND STAGE ---
    python "%BIN%\extract_second.py" --bin "%WORK%\block1_usbldr.bin" --out "%WORK%\second_out"
    if errorlevel 1 (
        echo Extract FAILED
        pause
        goto MENU
    )
    echo Extract OK
)

start explorer "%WORK%\second_out"
echo.
echo ============================================================
echo EDIT FILES IN THE OPENED FOLDER
echo Press any key when done...
echo ============================================================
pause >nul

echo.
echo --- REPACKING SECOND STAGE ---
python "%BIN%\repack_inject.py" --bin "%WORK%\block1_usbldr.bin" --out "%WORK%\block1_patched.bin" --second "%WORK%\second_out"
if errorlevel 1 (
    echo Repack FAILED
    pause
    goto MENU
)
echo Repack OK

copy /Y "%WORK%\block1_patched.bin" "%WORK%\usbldr_unpacked\block1_usbldr.bin" >nul 2>&1
echo.
echo --- BUILDING FINAL LOADER ---
python "%BIN%\usbloader_packer.py" -p "%WORK%\usbldr_unpacked" -o "%OUTFILE%"
if errorlevel 1 (
    echo Build FAILED
    pause
    goto MENU
)

echo.
echo ==========================================
echo DONE: %OUTFILE%
echo ==========================================
pause
goto MENU

:AUTO_FAST
echo.
echo ==========================================
echo [91] FAST WORKFLOW
echo ==========================================

if not exist "%WORK%\second_out" (
    echo ERROR: No second stage folder found.
    echo Please run option 90 first to extract second stage.
    pause
    goto MENU
)

if not exist "%WORK%\block1_usbldr.bin" (
    echo ERROR: No block1 file found.
    echo Please run option 3 first to unpack.
    pause
    goto MENU
)

if not defined OUTFILE (
    if defined LOADER (
        for %%X in ("%LOADER%") do set "LOADER_NAME=%%~nX"
        set "OUTFILE=%OUT%\%LOADER_NAME%_patched.bin"
    ) else (
        set "OUTFILE=%OUT%\usbloader_patched.bin"
    )
)

if not exist "%WORK%\usbldr_unpacked\block0_raminit.bin" (
    echo Re-unpacking to restore missing files...
    python "%BIN%\usbloader_packer.py" -u "%WORK%\usbloader.bin" -d "%WORK%\usbldr_unpacked" >nul 2>&1
    copy /Y "%WORK%\usbldr_unpacked\block1_usbldr.bin" "%WORK%\block1_usbldr.bin" >nul 2>&1
)

echo.
echo --- REPACKING SECOND STAGE ---
python "%BIN%\repack_inject.py" --bin "%WORK%\block1_usbldr.bin" --out "%WORK%\block1_patched.bin" --second "%WORK%\second_out"
if errorlevel 1 (
    echo Repack FAILED
    pause
    goto MENU
)
echo Repack OK

copy /Y "%WORK%\block1_patched.bin" "%WORK%\usbldr_unpacked\block1_usbldr.bin" >nul 2>&1
echo.
echo --- BUILDING FINAL LOADER ---
python "%BIN%\usbloader_packer.py" -p "%WORK%\usbldr_unpacked" -o "%OUTFILE%"
if errorlevel 1 (
    echo Build FAILED
    pause
    goto MENU
)

echo.
echo ==========================================
echo DONE: %OUTFILE%
echo ==========================================
pause
goto MENU

:AUTO_PATCH
echo.
echo ==========================================
echo [92] PATCH WORKFLOW
echo ==========================================

if not exist "%WORK%\usbloader.bin" (
    if not defined LOADER (
        echo No loader found
        pause
        goto MENU
    )
    for %%X in ("%LOADER%") do set "LOADER_NAME=%%~nX"
    set "OUTFILE=%OUT%\%LOADER_NAME%_patched.bin"
    copy /Y "%LOADER%" "%WORK%\usbloader.bin" >nul 2>&1
    echo Source loaded
)

if not exist "%WORK%\usbldr_unpacked\metadata.txt" (
    echo.
    echo --- UNPACKING ---
    python "%BIN%\usbloader_packer.py" -u "%WORK%\usbloader.bin" -d "%WORK%\usbldr_unpacked"
    if errorlevel 1 (
        echo Unpack FAILED
        pause
        goto MENU
    )
    copy /Y "%WORK%\usbldr_unpacked\block1_usbldr.bin" "%WORK%\block1_usbldr.bin" >nul 2>&1
    echo Unpack OK
)

if not exist "%WORK%\second_out\.extract_meta" (
    echo.
    echo --- EXTRACTING SECOND STAGE ---
    python "%BIN%\extract_second.py" --bin "%WORK%\block1_usbldr.bin" --out "%WORK%\second_out"
    if errorlevel 1 (
        echo Extract FAILED
        pause
        goto MENU
    )
    echo Extract OK
)

if not exist "%WORK%\second_out\etc" mkdir "%WORK%\second_out\etc"
if exist "%BIN%\patchblocked.sh" (
    copy /Y "%BIN%\patchblocked.sh" "%WORK%\second_out\etc\" >nul 2>&1
    echo patchblocked.sh added to etc/
) else (
    echo WARNING: patchblocked.sh not found in bin folder
)

echo.
echo --- REPACKING SECOND STAGE ---
python "%BIN%\repack_inject.py" --bin "%WORK%\block1_usbldr.bin" --out "%WORK%\block1_patched.bin" --second "%WORK%\second_out"
if errorlevel 1 (
    echo Repack FAILED
    pause
    goto MENU
)
echo Repack OK

copy /Y "%WORK%\block1_patched.bin" "%WORK%\usbldr_unpacked\block1_usbldr.bin" >nul 2>&1
echo.
echo --- BUILDING FINAL LOADER ---
python "%BIN%\usbloader_packer.py" -p "%WORK%\usbldr_unpacked" -o "%OUTFILE%"
if errorlevel 1 (
    echo Build FAILED
    pause
    goto MENU
)

echo.
echo ==========================================
echo DONE: %OUTFILE%
echo ==========================================
pause
goto MENU

:: ==================== UTILITIES ====================

:CHECK
cls
echo.
echo -- Python scripts (bin\) --
if exist "%BIN%\usbloader_packer.py" (echo [OK] usbloader_packer.py) else echo [!!] MISSING
if exist "%BIN%\extract_second.py" (echo [OK] extract_second.py) else echo [!!] MISSING
if exist "%BIN%\repack_inject.py" (echo [OK] repack_inject.py) else echo [!!] MISSING
if exist "%BIN%\patchblocked.sh" (echo [OK] patchblocked.sh) else echo [  ] optional
echo.
echo -- Work files --
if exist "%WORK%\usbloader.bin" echo [OK] usbloader.bin
if exist "%WORK%\block1_usbldr.bin" echo [OK] block1_usbldr.bin
if exist "%WORK%\block1_patched.bin" echo [OK] block1_patched.bin
if exist "%WORK%\usbldr_unpacked\metadata.txt" echo [OK] unpacked
if exist "%WORK%\second_out\.extract_meta" echo [OK] second_out
if exist "%OUTFILE%" echo [OK] Final: %OUTFILE%
echo.
pause
goto MENU

:FLASH
echo.
echo ===== FLASH INSTRUCTIONS =====
echo 1. Short test point, connect USB
echo 2. Find COM port in Device Manager
echo.
echo For V7R22 (E5785/E5885/B525/B535) use: -x3
echo For V7R11 (E5573/E3372h/B310) use: -x2
echo.
if defined OUTFILE (
    echo Command: balong-usbdload.exe -p COMx -x3 "%OUTFILE%"
) else (
    echo Command: balong-usbdload.exe -p COMx -x3 output\*_patched.bin
)
echo.
echo Replace COMx with actual port number
pause
goto MENU

:VIEWLOG
if not exist "%LOG%" (
    echo No log file yet
    pause
    goto MENU
)
start notepad "%LOG%"
goto MENU

:CLEAN
set "CF="
set /p "CF=Type YES to delete work folder: "
if /i not "%CF%"=="YES" (
    echo Cancelled
    pause
    goto MENU
)
if exist "%WORK%\usbloader.bin" del /f /q "%WORK%\usbloader.bin"
if exist "%WORK%\block1_usbldr.bin" del /f /q "%WORK%\block1_usbldr.bin"
if exist "%WORK%\block1_patched.bin" del /f /q "%WORK%\block1_patched.bin"
if exist "%WORK%\usbldr_unpacked" rd /s /q "%WORK%\usbldr_unpacked"
if exist "%WORK%\second_out" rd /s /q "%WORK%\second_out"
set OUTFILE=
echo Work folder cleaned
pause
goto MENU