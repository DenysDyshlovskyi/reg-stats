Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
Write-Host "Starting script"

Start-Sleep -Seconds 10

# PowerShell script to update the code

# Import variables
$cd = Get-Location
$vars = Get-Content -Path "$cd\vars.json" | ConvertFrom-Json
$domainHttp = $vars.domain_http
$httpPrefix = $vars.http_prefix
$currentVersion = $vars.current_version
$masterKey = $vars.master_key
$clientId = $vars.client_id
$updateDirectory = "$mainLocation\update"
$downloadDirectory = "$mainLocation\download"
$mainLocation = $vars.main_location
$pythonPid = Get-Content -Path "$cd\pid.txt" -Force

# Do post request to check for new version
$postUrl = "$httpPrefix$domainHttp/api/get_update"

# Create json structure for post request
$postData = @{
    "masterKey" = $masterKey
    "clientId" = $clientId
    "currentVersion" = $currentVersion
} | ConvertTo-Json

# Check if update directory exists
if (!(Test-Path -Path "$updateDirectory" -PathType Container)) {
    Write-Host "Created update directory"
    New-Item -Path "$updateDirectory" -ItemType Directory -Force
}

# Check if download directory exists
if (!(Test-Path -Path "$downloadDirectory" -PathType Container)) {
    Write-Host "Created download directory"
    New-Item -Path "$downloadDirectory" -ItemType Directory -Force
}

# Removes all update and download files
function cleanup {
    Write-Host "Doing cleanup"
    if (Test-Path -Path "$updateDirectory" -PathType Container) {
        Remove-Item -Path "$updateDirectory" -Force -Recurse
    }
    if (Test-Path -Path "$downloadDirectory" -PathType Container) {
        Remove-Item -Path "$downloadDirectory" -Force -Recurse
    }
}

# Post to server
try{
    Write-Host "Posting to $postUrl"
    Invoke-WebRequest -Uri "$postUrl" -Method Post -Body $postData -ContentType "application/json" -OutFile "$downloadDirectory\update.zip"
    try {
        # Update is available, extract it
        Remove-Item -Path "$updateDirectory\*" -Force -Recurse
        Expand-Archive -Path "$downloadDirectory\update.zip" -DestinationPath "$updateDirectory" -Force

        # Stop python process
        if (Get-Process -Id $pythonPid) {
            Stop-Process -Id $pythonPid -Force
        }

        # Replace all files with the ones in the update
        Copy-Item -Path "$updateDirectory\*" -Destination "$mainLocation" -Force

        # Check if client id still exists in vars.json
        $newVars = Get-Content -Path "$mainLocation\vars.json" | ConvertFrom-Json
        if (!($newVars | Get-Member -Name "client_id")) {
            $newVars | Add-Member -MemberType NoteProperty -Name client_id -Value $clientId
        }
        Set-Content -Path "$mainLocation\vars.json" -Value ($newVars | ConvertTo-Json) -Force

        # Start the python script
        Start-Process -FilePath "$mainLocation\run.bat"

        cleanup
    } catch {
        # Update is not available or something went wrong, roll back
        Write-Error $_
        cleanup
    }
} catch {
    Write-Error $_
    cleanup
}

Pause