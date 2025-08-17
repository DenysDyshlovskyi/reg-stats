@ECHO OFF

if exist D:\RegStats D:
if exist E:\RegStats E:
if exist F:\RegStats F:
if exist G:\RegStats G:

cd RegStats\scripts
Powershell.exe -executionpolicy Unrestricted -File RunInstall.ps1