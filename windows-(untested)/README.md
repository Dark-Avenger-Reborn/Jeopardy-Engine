##  COMPILE, INSTALL, AND VERIFY THE DRIVER

---

###  STEP 1: Set Up Your Environment

**Required Tools (already installed or install them):**

* **Visual Studio (Community Edition)**
* **Windows Driver Kit (WDK)** — matching your OS version
   [WDK Downloads](https://learn.microsoft.com/en-us/windows-hardware/drivers/download-the-wdk)

---

###  STEP 2: Build the Driver

1. Open **Visual Studio**

2. Create a new project:
   **Kernel Mode Driver, Empty (KMDF)**

3. Name the project `IntelFWMonitor` (or similar)

4. Replace the auto-generated `.c` file with your `SimpleDriver.c`

5. Set **build settings**:

   * Configuration: `Release`
   * Platform: `x64`
   * Entry point: `DriverEntry` (in Linker → Advanced)
   * Runtime library: `/MT` (in C/C++ → Code Generation)

6. Build the project → Outputs:
   `IntelFWMonitor.sys` in `x64\Release\`

7. Copy the `.sys` file to:

```
C:\ProgramData\Intel\fwupdate\fw.sys
```

(Create directories as needed)

---

### STEP 3: Run the Installer Script as SYSTEM

1. Download **PsExec** from Sysinternals:
   [https://learn.microsoft.com/en-us/sysinternals/downloads/psexec](https://learn.microsoft.com/en-us/sysinternals/downloads/psexec)

2. Open Command Prompt **as Administrator**

3. Launch a SYSTEM shell:

```cmd
psexec -i -s powershell.exe
```

4. In the SYSTEM PowerShell session, run:

```powershell
& "C:\ProgramData\Intel\fwupdate\install.ps1"
```

---

###  STEP 4: Verify the Driver Is Loaded

#### Option 1: Check with `sc`

```cmd
sc query IntelFWMonitor
```

Look for:

```
STATE: 4 RUNNING
```

#### Option 2: Use Device Manager (Hidden Devices)

1. Open Device Manager
2. View → Show Hidden Devices
3. Look under **Non-Plug and Play Drivers** → `IntelFWMonitor` (or your service name)

---

###  STEP 5: View Driver Logs

1. Download **DebugView** from Sysinternals:
   [https://learn.microsoft.com/en-us/sysinternals/downloads/debugview](https://learn.microsoft.com/en-us/sysinternals/downloads/debugview)

2. Run DebugView **as administrator**

3. You should see:

```
[IntelFWMonitor] Driver loaded successfully
```

Unloading will show:

```
[IntelFWMonitor] Driver unloaded
```

---

###  STEP 6: Uninstall (If Needed)

From Admin PowerShell:

```powershell
Stop-Service IntelFWMonitor
sc delete IntelFWMonitor
Remove-Item -Path "C:\ProgramData\Intel\fwupdate\fw.sys" -Force
```
