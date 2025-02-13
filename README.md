# Jeopardy Engine 🚀

A tool to manage and automate services during the [Lockdown Cybersecurity Competition](https://lockdown.ubnetdef.org/) using Ansible playbooks. This repository enables real-time service management via a Flask web application.

## Overview

This repository contains code designed to manage and automate various tasks related to the UB Net Def cybersecurity competition. The core logic uses **Ansible** playbooks to control services across different hosts. The system uses Flask with **SocketIO** for real-time communication to interact with users, allowing them to "break" or "fix" services on virtual machines during the competition.

## Features

- **Automated service management** using Ansible playbooks.
- **Real-time status updates** using Flask and SocketIO. 🔄
- **Multiple teams management** with distinct service sets. 🏆
- **Web interface** for easy interaction to control services. 🌐
- **Break and fix playbooks** for controlling the state of services on remote hosts. ⚙️

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Dark-Avenger-Reborn/Jeopardy-Engine.git
cd Jeopardy-Engine
```

### 2. Install the required dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Ansible Inventory

- Modify the `realinv.ini` file to match your hosts and variables.
- If you are using this for the UB Net Def cybersecurity competition you may use the exisiting file.

### 4. Running the Application

Run the Flask app:

```bash
python main.py
```

Access the app by visiting `http://localhost:5000` in your web browser. 🌍

## How It Works

- The application allows users to interact with a Scoring Engine replicate which allows them to controll services in real-time during the competition. 🎮
- Users can toggle the "break" or "fix" state of services using checkboxes.
- Each action triggers the execution of an Ansible playbook to stop or start services.
- The web interface updates live as the state of services changes. 🔧

## Contributing 🤝

If you would like to contribute to this project, please fork the repository and submit a pull request with your changes.

## License 📝

This project is licensed under the Apache License 2.0 License - see the [LICENSE](LICENSE) file for details.
