# Set correct working directory
if (Test-Path -Path "D:\RegStats" -PathType Container) { Set-Location D:\RegStats }
if (Test-Path -Path "E:\RegStats" -PathType Container) { Set-Location E:\RegStats }
if (Test-Path -Path "F:\RegStats" -PathType Container) { Set-Location F:\RegStats }
if (Test-Path -Path "G:\RegStats" -PathType Container) { Set-Location G:\RegStats }

$cd = Get-Location

# import vars.json
$vars = Get-Content -Path "$cd\client\vars.json" | ConvertFrom-Json

# Create folder if it does not exist
$mainLocation = $vars.main_location
if (!(Test-Path -Path "$mainLocation" -PathType Container -ErrorAction SilentlyContinue)) {
    New-Item -ItemType Directory -Path "$mainLocation" -Force
    Write-Host "Created folder $mainLocation"
}

# Copy contents to folder
Copy-Item -Path "$cd\client\*" -Destination $mainLocation -Recurse -Force
Write-Host "Copied items into $mainLocation"

# Make post request to register client in database
try {
    $ipDomain = $vars.domain_http
    $masterKey = $vars.master_key
    $postUrl = "http://$ipDomain/api/register"

    # Create json structure with relevant info
    $postData = @{
        "username" = $env:USERNAME
        "domain" = $env:USERDOMAIN
        "computerName" = $env:COMPUTERNAME
        "masterKey" = $masterKey
    } | ConvertTo-Json

    # Post to server
    $response = Invoke-RestMethod -Uri "$postUrl" -Method Post -Body $postData -ContentType "application/json"
    if ($response.code -ne "OK") {
        Write-Error "Something went wrong while posting: $response"
        Read-Host "Press enter to continue..."
        exit
    }

    # Get client id and add it to vars.json
    $clientId = $response.client_id
    $vars | Add-Member -Type NoteProperty -Name "client_id" -Value $clientId
    Set-Content -Path "$mainLocation\vars.json" -Value ($vars | ConvertTo-Json) -Force

    # Create shortcut in startup folder
    $WshShell = New-Object -COMObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\RegStats.lnk")
    $Shortcut.TargetPath = "$mainLocation\REG Stats Client.exe"
    $Shortcut.WorkingDirectory = "$mainLocation"
    $Shortcut.Save()

    Write-Host "Created shortcut to exe in startup folder"

    # Script is done, start exe, unblock files
    foreach ($file in Get-ChildItem -Path $mainLocation -File -Recurse) {
        Unblock-File -Path $file.FullName
    }
    Start-Process -FilePath "$mainLocation\REG Stats Client.exe"

    Read-Host "Script done, press enter to exit..."
    exit
} catch {
    Write-Error "Something went wrong: $_"
    Read-Host "Press enter to continue..."
    exit
}