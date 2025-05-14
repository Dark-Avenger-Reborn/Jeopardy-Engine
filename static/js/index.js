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

  let term = null;
  let terminalOpened = false;
  let pendingAction = null;

  // Show Terminal
  showTerminalBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    terminalBox.style.display = "block";

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

      const socket = io("/logs");
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
      event.target !== showTerminalBtn
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
      const controlSocket = io("/control");
      controlSocket.emit("server_action", { action: pendingAction });
    }
    confirmationModal.classList.add("hidden");
    pendingAction = null;
  });

  confirmNo.addEventListener("click", function () {
    confirmationModal.classList.add("hidden");
    pendingAction = null;
  });
});
