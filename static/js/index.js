document.addEventListener("DOMContentLoaded", function () {
  // Terminal Setup
  const terminalContainer = document.getElementById("terminal");
  const terminalBox = document.getElementById("terminal-container");
  const showTerminalBtn = document.getElementById("show-terminal");
  const gearBtn = document.getElementById("gearBtn");
  const dropdownMenu = document.getElementById("dropdownMenu");
  const confirmationModal = document.getElementById("confirmationModal");
  const confirmationText = document.getElementById("confirmationText");
  const confirmYes = document.getElementById("confirmYes");
  const confirmNo = document.getElementById("confirmNo");
  const errorModal = document.getElementById("errorModal");
  const errorText = document.getElementById("errorText");
  const errorCloseBtn = document.getElementById("errorCloseBtn");
  const levelStatus = document.getElementById("level-status");
  const isAdminPage = window.location.pathname === "/admin";

  let term = null;
  let terminalOpened = false;
  let pendingAction = null;
  let terminalLogBuffer = "";

  const noisyLogPatterns = [
    /\"(GET|POST) \/socket\.io\//,
    /^\(\d+\) accepted \('/,
  ];

  function shouldHideLogLine(line) {
    return noisyLogPatterns.some((pattern) => pattern.test(line));
  }

  function writeTerminalLogChunk(text) {
    if (!term || typeof text !== "string") {
      return;
    }

    terminalLogBuffer += text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    const lines = terminalLogBuffer.split("\n");
    terminalLogBuffer = lines.pop();

    lines.forEach((line) => {
      if (!line.trim() || shouldHideLogLine(line)) {
        return;
      }
      term.writeln(line);
    });
  }

  // ✅ Create single socket connection here
  const socket = io(); // Adjust namespace only if required, e.g., io("/some-namespace")

  function setLevelStatus(message, type = "") {
    if (!levelStatus) {
      return;
    }
    levelStatus.textContent = message;
    levelStatus.className = `level-status ${type}`.trim();
  }

  // Show Terminal
  showTerminalBtn.addEventListener("click", function (e) {
    e.stopPropagation();

    if (isAdminPage) {
      if (!terminalOpened) {
        initTerminal();
      }
      terminalBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
      return;
    }

    if (terminalBox.style.display === "block") {
      terminalBox.style.display = "none";
      return;
    } else {
      terminalBox.style.display = "block";
    }

    if (!terminalOpened) {
      term = new Terminal({
        cursorBlink: true,
        fontFamily: "monospace",
        fontSize: 14,
        theme: {
          background: "#1e1e1e",
          foreground: "#f5f5f5",
        },
      });

      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(terminalContainer);
      term.write("Server log will appear here...\r\n");

      const dimensions = fitAddon.proposeDimensions();
      if (dimensions?.cols && dimensions?.rows) {
        term.resize(dimensions.cols, dimensions.rows);
      }

      socket.on("log_output", (msg) => {
        writeTerminalLogChunk(msg.data || "");
      });

      terminalOpened = true;
    }
  });

  // Hide Terminal & Dropdown on Outside Click
  document.addEventListener("mousedown", function (event) {
    if (
      !isAdminPage &&
      terminalBox.style.display === "block" &&
      !terminalBox.contains(event.target) &&
      !showTerminalBtn.contains(event.target)
    ) {
      terminalBox.style.display = "none";
    }

    if (
      dropdownMenu.classList.contains("show") &&
      !dropdownMenu.contains(event.target) &&
      !gearBtn.contains(event.target)
    ) {
      dropdownMenu.classList.remove("show");
    }
  });

  // Toggle Dropdown
  gearBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    dropdownMenu.classList.toggle("show");
  });

  // Server Action Buttons with Modal
  document.querySelectorAll(".server-action").forEach((button) => {
    button.addEventListener("click", function () {
      const action = button.dataset.action;
      let message = "";

      switch (action) {
        case "restart_service":
          message = "Are you sure you want to restart the interface/service?";
          break;
        case "reboot":
          message = "Are you sure you want to reboot the server?";
          break;
        case "shutdown":
          message = "Are you sure you want to shutdown the server?";
          break;
      }

      if (message) {
        confirmationText.textContent = message;
        confirmationModal.classList.remove("hidden");
        pendingAction = action;
      }
    });
  });

  // Modal Confirmation
  confirmYes.addEventListener("click", function () {
    if (pendingAction) {
      // ✅ Use the same socket
      socket.emit("server_action", { action: pendingAction });
    }
    confirmationModal.classList.add("hidden");
    pendingAction = null;
  });

  confirmNo.addEventListener("click", function () {
    confirmationModal.classList.add("hidden");
    pendingAction = null;
  });

  // Admin Button
  const adminBtn = document.getElementById("admin-btn");
  if (adminBtn) {
    adminBtn.addEventListener("click", function () {
      window.location.href = isAdminPage ? "/" : "/admin";
    });
  }

  // Level Select
  const levelSelect = document.getElementById("level-select");
  if (levelSelect) {
    levelSelect.addEventListener("change", async function () {
      const level = levelSelect.value;
      levelSelect.disabled = true;
      setLevelStatus("Switching break level and clearing active breaks...", "pending");

      try {
        const response = await fetch("/set_level", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ level }),
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.message || "Failed to switch break level.");
        }

        document.getElementById("current-level").textContent = data.level || level;
        if (data.scoreboard && data.systems && data.all_services) {
          scoreboardData = data.scoreboard;
          systems = data.systems;
          allServices = data.all_services;
          renderScoreboard();
        }
        setLevelStatus(data.message || `Break level changed to ${level}.`, "success");
      } catch (err) {
        setLevelStatus(err.message || "Unable to change break level.", "error");
        showError(err.message || "Unable to change break level.");
      } finally {
        levelSelect.disabled = false;
      }
    });
  }

  // Redboard Button Logic
  const protectiveCap = document.getElementById("protective-cap");
  const redboardBtn = document.getElementById("redboard-btn");
  let capOpen = false;

  if (protectiveCap) {
    protectiveCap.addEventListener("click", function () {
      capOpen = !capOpen;
      protectiveCap.classList.toggle("open");
      checkRedboardReady();
    });
  }

  function checkRedboardReady() {
    if (!redboardBtn) {
      return;
    }

    if (capOpen) {
      redboardBtn.classList.remove("locked");
      redboardBtn.setAttribute("aria-disabled", "false");
    } else {
      redboardBtn.classList.add("locked");
      redboardBtn.setAttribute("aria-disabled", "true");
    }
  }

  if (redboardBtn) {
    checkRedboardReady();

    redboardBtn.addEventListener("click", function () {
      if (redboardBtn.classList.contains("locked")) {
        setLevelStatus("Open the SEALED cap before firing Redboard.", "pending");
        return;
      }

      fetch("/redboard")
        .then(response => response.text())
        .then(data => setLevelStatus(data, "success"))
        .catch(() => showError("Unable to deploy redboard break."));
    });
  }

  // If admin, init terminal immediately
  if (isAdminPage) {
    initTerminal();
  }

  function initTerminal() {
    if (!terminalOpened) {
      term = new Terminal({
        cursorBlink: true,
        fontFamily: "monospace",
        fontSize: 14,
        theme: {
          background: "#1e1e1e",
          foreground: "#f5f5f5",
        },
      });

      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(terminalContainer);
      term.write("Server log will appear here...\r\n");

      const dimensions = fitAddon.proposeDimensions();
      if (dimensions?.cols && dimensions?.rows) {
        term.resize(dimensions.cols, dimensions.rows);
      }

      socket.on("log_output", (msg) => {
        writeTerminalLogChunk(msg.data || "");
      });

      terminalOpened = true;
    }
    terminalBox.style.display = "block";
  }

  function showError(message) {
    errorText.textContent = message;
    errorModal.classList.remove("hidden");
  }

  errorCloseBtn.addEventListener("click", function () {
    errorModal.classList.add("hidden");
  });

  socket.on("connect_error", () => {
    showError("Unable to connect to server. Please check your connection.");
  });

  socket.on("server_error", (data) => {
    console.error("Server error:", data);
    showError(data.message || "An unexpected server error occurred.");
  });

  let scoreboardData = [];
  let systems = [];
  let allServices = [];
  const scoreboardHead = document.getElementById("scoreboardHead");
  const scoreboardBody = document.getElementById("scoreboardBody");

  function renderScoreboard() {
    // Build an array of all protocols in order
    const allProtocols = [];
    systems.forEach((system) => {
      if (system.protocols && system.protocols.length > 0) {
        system.protocols.forEach((protocol) => {
          allProtocols.push({ system: system.name, protocol: protocol });
        });
      }
    });
    
    console.log('Systems count:', systems.length);
    console.log('All protocols count:', allProtocols.length);
    console.log('Last protocol:', allProtocols[allProtocols.length - 1]);

    // Render header rows
    if (scoreboardHead) {
      scoreboardHead.innerHTML = "";
      
      // First header row: System names with colspan
      const systemHeaderRow = document.createElement("tr");
      const teamHeaderCell = document.createElement("th");
      teamHeaderCell.textContent = "";
      teamHeaderCell.className = "team-header-cell";
      systemHeaderRow.appendChild(teamHeaderCell);
      
      systems.forEach((system) => {
        // Skip systems with no protocols
        if (!system.protocols || system.protocols.length === 0) {
          return;
        }
        const th = document.createElement("th");
        th.textContent = system.name;
        th.className = "system-group-header";
        const protocolCount = system.protocols.length;
        th.colSpan = protocolCount;
        systemHeaderRow.appendChild(th);
      });
      scoreboardHead.appendChild(systemHeaderRow);
      
      // Second header row: Protocol names
      const protocolHeaderRow = document.createElement("tr");
      const emptyCell = document.createElement("th");
      emptyCell.className = "team-header-cell";
      protocolHeaderRow.appendChild(emptyCell);
      
      allProtocols.forEach((item) => {
        const th = document.createElement("th");
        th.textContent = item.protocol;
        th.className = "protocol-header";
        protocolHeaderRow.appendChild(th);
      });
      scoreboardHead.appendChild(protocolHeaderRow);
    }

    // Render team rows with checkmarks
    if (scoreboardBody) {
      scoreboardBody.innerHTML = "";
      
      scoreboardData.forEach((teamData, teamIdx) => {
        const row = document.createElement("tr");
        
        // Team name cell
        const teamCell = document.createElement("td");
        teamCell.textContent = teamData.team || `Team ${teamIdx + 1}`;
        row.appendChild(teamCell);
        
        // Protocol cells with checkmarks
        allProtocols.forEach((item) => {
          const cell = document.createElement("td");
          cell.className = "protocol-cell";
          
          const serviceKey = `${item.system}:${item.protocol}`;
          const serviceIdx = allServices.indexOf(serviceKey);
          
          // Check if this service is "broken" for this team
          if (serviceIdx !== -1 && teamData.services[serviceIdx]) {
            cell.classList.add("active");
            cell.textContent = "✓";
          } else {
            cell.classList.add("inactive");
            cell.textContent = "—";
          }
          
          cell.addEventListener("click", () => {
            if (serviceIdx !== -1) {
              socket.emit("toggle_service", {
                team_idx: teamIdx,
                service_idx: serviceIdx,
              });
            }
          });
          
          row.appendChild(cell);
        });
        
        scoreboardBody.appendChild(row);
      });
    }
  }

  // Listen for scoreboard updates from server
  socket.on("scoreboard_update", (msg) => {
    scoreboardData = msg.scoreboard || [];
    systems = msg.systems || [];
    allServices = msg.all_services || [];
    renderScoreboard();
  });
});
