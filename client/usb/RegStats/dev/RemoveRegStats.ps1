# Set correct working directory
if (Test-Path -Path "D:\RegStats" -PathType Container) { Set-Location D:\RegStats }
if (Test-Path -Path "E:\RegStats" -PathType Container) { Set-Location E:\RegStats }
if (Test-Path -Path "F:\RegStats" -PathType Container) { Set-Location F:\RegStats }
if (Test-Path -Path "G:\RegStats" -PathType Container) { Set-Location G:\RegStats }

$cd = Get-Location

# import vars.json and main location
$vars = Get-Content -Path "$cd\client\vars.json" | ConvertFrom-Json
$mainLocation = $vars.main_location
$ipDomain = $vars.domain_http
$masterKey = $vars.master_key

# Check if location exists
if (!(Test-Path -Path "$mainLocation" -PathType Container -ErrorAction SilentlyContinue)) {
    Write-Error "Error: $mainLocation does not exist"
    Read-Host "Press enter to continue..."
    exit
}

# Get vars thats on client side and get client id
$varsClient = Get-Content -Path "$mainLocation\vars.json" | ConvertFrom-Json
$clientId = $varsClient.client_id

# If the exe is running, kill it
if (Get-Process -Name "REG Stats Client" -ErrorAction SilentlyContinue) {
    Stop-Process -Name "REG Stats Client" -Force
    Write-Host "Killed reg stats client process"
}

# Post to server to remove client from database
$postUrl = "http://$ipDomain/api/remove_client"
$postData = @{
    "clientId" = $clientId
    "masterKey" = $masterKey
} | ConvertTo-Json
Invoke-RestMethod -Uri "$postUrl" -Method Post -Body $postData -ContentType "application/json" -ErrorAction SilentlyContinue

# Remove startup link
if (Test-Path -Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\RegStats.lnk" -ErrorAction SilentlyContinue) {
    Remove-Item -Path "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\RegStats.lnk" -Force
    Write-Host "Startup link removed"
}

# Delete all files in main location
Get-ChildItem -Path "$mainLocation" | ForEach-Object {
    try {
        Remove-Item -Path $_.FullName -Force
    } catch {
        Write-Error "Failed to delete file: $_"
    }
}

# Remove main location directory
Remove-Item -Path $mainLocation -Force

Read-Host "Script done, press enter to continue..."
exit