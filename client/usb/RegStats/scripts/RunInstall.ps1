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

    # Get public ip adress
    try {
        $publicIpResponse = Invoke-RestMethod -Uri "https://api.ipify.org?format=json"
        $publicIP = $publicIpResponse.ip
    } catch {
        $publicIP = "Unavailable"
    }

    # Get cpu name
    $cpuName = (Get-CimInstance -ClassName Win32_Processor).Name

    # Get ram details
    $ramInfo = Get-CimInstance -ClassName Win32_PhysicalMemory

    # Get ddr type
    $ddrType = "DDR"
    if ($ramInfo.ConfiguredVoltage -eq 1200) {
        $ddrType = "DDR4"
    } elseif ($ramInfo.ConfiguredVoltage -eq 1500) {
        $ddrType = "DDR3"
    } elseif ($ramInfo.ConfiguredVoltage -eq 1800) {
        $ddrType = "DDR2"
    } elseif ($ramInfo.ConfiguredVoltage -gt 1800) {
        $ddrType = "DDR"
    } elseif ($ramInfo.ConfiguredVoltage -lt 1200) {
        $ddrType = "DDR5"
    }

    # Get capacity
    $ramCapacity = ($ramInfo.Capacity / [Math]::Pow(1024,3))

    # Put everything together
    $ramName = '{0} {1} {2}GB {3}MHz {4}' -f $ramInfo.Manufacturer, $ddrType, $ramCapacity, $ramInfo.ConfiguredClockSpeed, $ramInfo.SerialNumber

    # Get serial number
    $serialNumber = (Get-WmiObject -Class Win32_BIOS | Select-Object -Property SerialNumber).SerialNumber

    # Get manufacturer
    $manufacturer = (Get-WmiObject -Class Win32_BIOS | Select-Object -Property Manufacturer).Manufacturer

    # Create json structure with all pc info
    $pcInfo = @{
        username = "$env:USERNAME"
        computer_name = "$env:COMPUTERNAME"
        onedrive_path = "$env:OneDrive"
        onedrive_path_commercial = "$env:OneDriveCommercial"
        domain = "$env:USERDOMAIN"
        os = "$env:OS"
        cpu = "$cpuName"
        ram = "$ramName"
        public_ip = "$publicIP"
        serialNumber = "$serialNumber"
        manufacturer = "$manufacturer"
    } | ConvertTo-Json

    # Create json structure for post request
    $postData = @{
        "masterKey" = $masterKey
        "pcInfo" = $pcInfo
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
    $Shortcut.TargetPath = "$mainLocation\run.bat"
    $Shortcut.WorkingDirectory = "$mainLocation"
    $Shortcut.Save()

    Write-Host "Created shortcut to exe in startup folder"

    # Script is done, start exe, unblock files
    foreach ($file in Get-ChildItem -Path $mainLocation -File -Recurse) {
        Unblock-File -Path $file.FullName
    }

    Start-Process -FilePath "$mainLocation\run.bat" -WorkingDirectory "$mainLocation"

    Read-Host "Script done, press enter to exit..."
    exit
} catch {
    Write-Error "Something went wrong: $_"
    Read-Host "Press enter to continue..."
    exit
}