@echo off
setlocal enableextensions disabledelayedexpansion

:: Get the current directory path
SET CURRENT_DIR=%~dp0
SET CURRENT_DIR=%CURRENT_DIR:~0,-1%

:: Define the string to be replaced and the current directory path
set "search=C:/HdriHaven"
set "replace=%CURRENT_DIR:\=/%"

set "files=main.py get_path.py shelf.py"

:: Find and replace the path
for %%f in (%files%) do (
	>"%%f.new" (
	  for /f "delims=" %%i in ('findstr /n "^" "%%f"') do (
		  set "line=%%i"
		  setlocal enabledelayedexpansion
		  set "line=!line:*:=!"
		  if defined line set "line=!line:%search%=%replace%!"
		  echo(!line!
		  endlocal
	  )
	)
	move /y "%%f.new" "%%f" >nul
)

:: Define the string to be replaced and the current inventory path
set "search=C:/HdriHaven/inventory"
set "replace=%CURRENT_DIR:\=/%/inventory"

set "file=settings.json"

:: Find and replace the path
>"%file%.new" (
  for /f "delims=" %%i in ('findstr /n "^" "%file%"') do (
	  set "line=%%i"
	  setlocal enabledelayedexpansion
	  set "line=!line:*:=!"
	  if defined line set "line=!line:%search%=%replace%!"
	  echo(!line!
	  endlocal
  )
)
move /y "%file%.new" "%file%" >nul
