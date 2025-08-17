@ECHO OFF

if exist D:\RegStats D:
if exist E:\RegStats E:
if exist F:\RegStats F:
if exist G:\RegStats G:
goto:end

:end
cd RegStats\dev
Powershell.exe -executionpolicy Unrestricted -File RemoveRegStats.ps1

:timeout
timeout /t 999