const socket = io();
socket.connect(window.location.origin);

document.addEventListener("DOMContentLoaded", () => {
const teams = [
    {
    name: "Team 01",
    ipAddresses: [
        "10.1.1.60", "10.1.1.60:389","10.1.2.2:80","10.1.2.10",
        "10.1.2.10:22","10.1.2.4:21","10.1.1.10","10.1.1.10:22",
        "10.1.1.40","10.1.1.40:22","10.1.1.30:80","10.1.1.30:3306",
        "10.1.1.70","10.1.1.70:5985","10.1.1.80","10.1.1.80:5985",
    ],
    },
    {
    name: "Team 02",
    ipAddresses: [
        "10.2.1.60","10.2.1.60:389","10.2.2.2:80","10.2.2.10",
        "10.2.2.10:22","10.2.2.4:21","10.2.1.10","10.2.1.10:22",
        "10.2.1.40","10.2.1.40:22","10.2.1.30:80","10.2.1.30:3306",
        "10.2.1.70","10.2.1.70:5985","10.2.1.80","10.2.1.80:5985",
    ],
    },
    {
    name: "Team 03",
    ipAddresses: [
        "10.3.1.60","10.3.1.60:389","10.3.2.2:80","10.3.2.10",
        "10.3.2.10:22","10.3.2.4:21","10.3.1.10","10.3.1.10:22",
        "10.3.1.40","10.3.1.40:22","10.3.1.30:80","10.3.1.30:3306",
        "10.3.1.70","10.3.1.70:5985","10.3.1.80","10.3.1.80:5985",
    ],
    },
    {
    name: "Team 04",
    ipAddresses: [
        "10.4.1.60","10.4.1.60:389","10.4.2.2:80","10.4.2.10",
        "10.4.2.10:22","10.4.2.4:21","10.4.1.10","10.4.1.10:22",
        "10.4.1.40","10.4.1.40:22","10.4.1.30:80","10.4.1.30:3306",
        "10.4.1.70","10.4.1.70:5985","10.4.1.80","10.4.1.80:5985",
    ],
    },
    {
    name: "Team 05",
    ipAddresses: [
        "10.5.1.60","10.5.1.60:389","10.5.2.2:80","10.5.2.10",
        "10.5.2.10:22","10.5.2.4:21","10.5.1.10","10.5.1.10:22",
        "10.5.1.40","10.5.1.40:22","10.5.1.30:80","10.5.1.30:3306",
        "10.5.1.70","10.5.1.70:5985","10.5.1.80","10.5.1.80:5985",
    ],
    },
    {
    name: "Team 06",
    ipAddresses: [
        "10.6.1.60","10.6.1.60:389","10.6.2.2:80","10.6.2.10",
        "10.6.2.10:22","10.6.2.4:21","10.6.1.10","10.6.1.10:22",
        "10.6.1.40","10.6.1.40:22","10.6.1.30:80","10.6.1.30:3306",
        "10.6.1.70","10.6.1.70:5985","10.6.1.80","10.6.1.80:5985",
    ],
    },
    {
    name: "Team 07",
    ipAddresses: [
        "10.7.1.60","10.7.1.60:389","10.7.2.2:80","10.7.2.10",
        "10.7.2.10:22","10.7.2.4:21","10.7.1.10","10.7.1.10:22",
        "10.7.1.40","10.7.1.40:22","10.7.1.30:80","10.7.1.30:3306",
        "10.7.1.70","10.7.1.70:5985","10.7.1.80","10.7.1.80:5985",
    ],
    },
    {
    name: "Team 08",
    ipAddresses: [
        "10.8.1.60","10.8.1.60:389","10.8.2.2:80","10.8.2.10",
        "10.8.2.10:22","10.8.2.4:21","10.8.1.10","10.8.1.10:22",
        "10.8.1.40","10.8.1.40:22","10.8.1.30:80","10.8.1.30:3306",
        "10.8.1.70","10.8.1.70:5985","10.8.1.80","10.8.1.80:5985",
    ],
    },
    {
    name: "Team 09",
    ipAddresses: [
        "10.9.1.60","10.9.1.60:389","10.9.2.2:80","10.9.2.10",
        "10.9.2.10:22","10.9.2.4:21","10.9.1.10","10.9.1.10:22",
        "10.9.1.40","10.9.1.40:22","10.9.1.30:80","10.9.1.30:3306",
        "10.9.1.70","10.9.1.70:5985","10.9.1.80","10.9.1.80:5985",
    ],
    },
    {
    name: "Team 10",
    ipAddresses: [
        "10.10.1.60","10.10.1.60:389","10.10.2.2:80","10.10.2.10",
        "10.10.2.10:22","10.10.2.4:21","10.10.1.10","10.10.1.10:22",
        "10.10.1.40","10.10.1.40:22","10.10.1.30:80","10.10.1.30:3306",
        "10.10.1.70","10.10.1.70:5985","10.10.1.80","10.10.1.80:5985",
    ],
    },
    {
    name: "Team 11",
    ipAddresses: [
        "10.11.1.60","10.11.1.60:389","10.11.2.2:80","10.11.2.10",
        "10.11.2.10:22","10.11.2.4:21","10.11.1.10","10.11.1.10:22",
        "10.11.1.40","10.11.1.40:22","10.11.1.30:80","10.11.1.30:3306",
        "10.11.1.70","10.11.1.70:5985","10.11.1.80","10.11.1.80:5985",
    ],
    },
    {
    name: "Team 12",
    ipAddresses: [
        "10.12.1.60","10.12.1.60:389","10.12.2.2:80","10.12.2.10",
        "10.12.2.10:22","10.12.2.4:21","10.12.1.10","10.12.1.10:22",
        "10.12.1.40","10.12.1.40:22","10.12.1.30:80","10.12.1.30:3306",
        "10.12.1.70","10.12.1.70:5985","10.12.1.80","10.12.1.80:5985",
    ],
    },
    {
    name: "Team 13",
    ipAddresses: [
        "10.13.1.60","10.13.1.60:389","10.13.2.2:80","10.13.2.10",
        "10.13.2.10:22","10.13.2.4:21","10.13.1.10","10.13.1.10:22",
        "10.13.1.40","10.13.1.40:22","10.13.1.30:80","10.13.1.30:3306",
        "10.13.1.70","10.13.1.70:5985","10.13.1.80","10.13.1.80:5985",
    ],
    },
    {
    name: "Team 14",
    ipAddresses: [
        "10.14.1.60","10.14.1.60:389","10.14.2.2:80","10.14.2.10",
        "10.14.2.10:22","10.14.2.4:21","10.14.1.10","10.14.1.10:22",
        "10.14.1.40","10.14.1.40:22","10.14.1.30:80","10.14.1.30:3306",
        "10.14.1.70","10.14.1.70:5985","10.14.1.80","10.14.1.80:5985",
    ],
    },
    {
    name: "Team 15",
    ipAddresses: [
        "10.15.1.60","10.15.1.60:389","10.15.2.2:80","10.15.2.10",
        "10.15.2.10:22","10.15.2.4:21","10.15.1.10","10.15.1.10:22",
        "10.15.1.40","10.15.1.40:22","10.15.1.30:80","10.15.1.30:3306",
        "10.15.1.70","10.15.1.70:5985","10.15.1.80","10.15.1.80:5985",
    ],
    },
];

const teamRows = document.getElementById("team-rows");

// Generate table rows for each team
teams.forEach((team, index) => {
    let row = `<tr>
    <th>Team ${
    index + 1
    } <input class="styled-checkbox row-checkbox" type="checkbox" data-row="${
    index + 1
    }"></th>`;

    team.ipAddresses.forEach((ip) => {
    row += `<td class="green"><input class="styled-checkbox ip-checkbox" type="checkbox"><span>${ip}</span></td>`;
    });

    row += `</tr>`;
    teamRows.innerHTML += row;
});

// Handle column checkboxes
document
    .querySelectorAll('thead input[type="checkbox"]')
    .forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
        const columnIndex = checkbox.dataset.column;
        const isChecked = checkbox.checked;
        document
        .querySelectorAll(
            `tbody td:nth-child(${parseInt(columnIndex) + 1})`
        )
        .forEach((cell) => {
            const ipCheckbox = cell.querySelector(".ip-checkbox");
            cell.className = isChecked ? "red" : "green";
            ipCheckbox.checked = isChecked;
            // Emit update to server
            socket.emit("update_status", {
            type: "column",
            index: columnIndex,
            checked: isChecked,
            });
        });
    });
    });

// Handle row checkboxes
document
    .querySelectorAll("tbody input.row-checkbox")
    .forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
        const row = checkbox.closest("tr");
        const isChecked = checkbox.checked;
        row.querySelectorAll("td").forEach((cell) => {
        const ipCheckbox = cell.querySelector(".ip-checkbox");
        cell.className = isChecked ? "red" : "green";
        ipCheckbox.checked = isChecked;
        // Emit update to server
        const rowIndex = checkbox.dataset.row;
        socket.emit("update_status", {
            type: "row",
            index: rowIndex,
            checked: isChecked,
        });
        });
    });
    });

// Handle IP checkboxes
document
    .querySelectorAll("tbody input.ip-checkbox")
    .forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
        const cell = checkbox.closest("td");
        const isChecked = checkbox.checked;
        cell.className = isChecked ? "red" : "green";
        // Emit update to server
        const rowIndex = checkbox
        .closest("tr")
        .querySelector("input.row-checkbox").dataset.row;
        const columnIndex =
        Array.from(cell.parentNode.children).indexOf(cell) + 1;
        socket.emit("update_status", {
        type: "ip",
        row: rowIndex,
        column: columnIndex,
        checked: isChecked,
        });
    });
    });

// Listen for updates from the server
socket.on("update_status_all", (data) => {
    // Update based on received data
    if (data.type === "column") {
    document
        .querySelectorAll(`thead input[data-column="${data.index}"]`)
        .forEach((checkbox) => {
        checkbox.checked = data.checked;
        });
    document
        .querySelectorAll(
        `tbody td:nth-child(${parseInt(data.index) + 1})`
        )
        .forEach((cell) => {
        const ipCheckbox = cell.querySelector(".ip-checkbox");
        cell.className = data.checked ? "red" : "green";
        ipCheckbox.checked = data.checked;
        });
    } else if (data.type === "row") {
    document.querySelector(
        `tbody input[data-row="${data.index}"]`
    ).checked = data.checked;
    const row = document.querySelector(
        `tbody tr:nth-child(${data.index})`
    );
    row.querySelectorAll("td").forEach((cell) => {
        const ipCheckbox = cell.querySelector(".ip-checkbox");
        cell.className = data.checked ? "red" : "green";
        ipCheckbox.checked = data.checked;
    });
    } else if (data.type === "ip") {
    const row = document.querySelector(
        `tbody tr:nth-child(${data.row})`
    );
    const cell = row.querySelector(`td:nth-child(${data.column})`);
    const ipCheckbox = cell.querySelector(".ip-checkbox");
    cell.className = data.checked ? "red" : "green";
    ipCheckbox.checked = data.checked;
    }
});
});