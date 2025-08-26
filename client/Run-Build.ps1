$clientBaseDir = "$env:USERPROFILE\Documents\GitHub\reg-stats\client"
Set-Location -Path "$clientBaseDir\development"
$buildDir = "build"
$venvPython = ".\venv\Scripts\python.exe"
$pythonExe = (Get-Command python).Path
$output = "RegStatsClient.pyz"
$pyzPath = "$clientBaseDir\development\$output"

# Remove previous pyz
if (Test-Path $pyzPath -PathType Leaf) { Remove-Item -Force $pyzPath }

# Clean build dir
if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }
mkdir $buildDir

# Install dependencies
& $venvPython -m pip install -r requirements.txt --target $buildDir

# Copy source files
Copy-Item __main__.py $buildDir
Copy-Item *.py $buildDir

# Create pyz
python -m zipapp $buildDir -o $output -p $pythonExe

# Clean up
Remove-Item -Recurse -Force $buildDir

# Copy into usb
$usbClient = "$clientBaseDir\usb\RegStats\client"
if (Test-Path -Path "$usbClient\$output" -PathType Leaf) {Remove-Item -Path "$usbClient\$output" -Force}
Copy-Item -Path "$pyzPath" -Destination "$usbClient" -Force

# Change current version
$usbVars = Get-Content -Path "$usbClient\vars.json" | ConvertFrom-Json
$newVersion = [int]$usbVars.current_version + 1
$usbVars.current_version = $newVersion
Set-Content -Path "$usbClient\vars.json" -Value ($usbVars | ConvertTo-Json) -Force

Write-Host -BackgroundColor Yellow -ForegroundColor Black "New version is $newVersion. Update name would be 'update-$newVersion.zip'"
Read-Host "Press enter to exit"