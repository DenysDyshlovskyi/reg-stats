Dim WShell
Set WShell = CreateObject("WScript.Shell")
WShell.Run "Powershell.exe -executionpolicy remotesigned -File __MAINLOCATION__\update.ps1", 0
Set WShell = Nothing