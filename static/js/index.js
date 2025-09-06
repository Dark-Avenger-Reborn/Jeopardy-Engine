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

  let term = null;
  let terminalOpened = false;
  let pendingAction = null;

  // ✅ Create single socket connection here
  const socket = io(); // Adjust namespace only if required, e.g., io("/some-namespace")

  // Show Terminal
  showTerminalBtn.addEventListener("click", function (e) {
    e.stopPropagation();

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
        term.write(msg.data.replace(/\n/g, "\r\n"));
      });

      terminalOpened = true;
    }
  });

  // Hide Terminal & Dropdown on Outside Click
  document.addEventListener("mousedown", function (event) {
    if (
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
  const scoreboardBody = document.getElementById("scoreboardBody");

  function renderScoreboard() {
    [...scoreboardBody.rows].forEach((row, rowIndex) => {
      // Keep only the first cell
      while (row.cells.length > 1) {
        row.deleteCell(1);
      }
      const services = scoreboardData[rowIndex]?.services || [];
      services.forEach((isAvailable, colIndex) => {
        const td = document.createElement("td");
        td.textContent = isAvailable ? "✓" : "";
        td.className = isAvailable ? "checkmark" : "empty";
        td.style.cursor = "pointer";
        td.addEventListener("click", () => {
          // Emit toggle event to server
          socket.emit("toggle_service", { team_idx: rowIndex, service_idx: colIndex });
        });
        row.appendChild(td);
      });
    });
  }

  // Listen for scoreboard updates from server
  socket.on("scoreboard_update", (msg) => {
    scoreboardData = msg.scoreboard;
    renderScoreboard();
  });
});
