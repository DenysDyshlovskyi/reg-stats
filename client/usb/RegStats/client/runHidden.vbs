Dim WShell
Set WShell = CreateObject("WScript.Shell")
WShell.Run "__MAINLOCATION__\run.bat", 0
Set WShell = Nothing