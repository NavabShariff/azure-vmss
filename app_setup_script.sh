#!/bin/bash

# Script to set up the Flask application on a VM for Golden Image creation

# --- 1. Basic System Updates and Dependencies ---
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv git apache2-utils # apache2-utils for ab (apache benchmark) if needed

# --- 2. Application Deployment ---
APP_DIR="/opt/my_flask_app"
REPO_URL="https://github.com/NavabShariff/azure-vmss.git" # IMPORTANT: REPLACE WITH YOUR ACTUAL GIT REPO URL!
# If your repo is private, you'll need to configure SSH keys or a PAT in the cloud-init script
# or use a token in the URL (e.g., https://<TOKEN>@github.com/...) - not recommended for security.

echo "Cloning application from ${REPO_URL} to ${APP_DIR}..."
sudo git clone ${REPO_URL} ${APP_DIR}

# Set ownership to the non-root user (e.g., azureuser)
sudo chown -R azureuser:azureuser ${APP_DIR}
sudo chmod -R 755 ${APP_DIR}

# --- 3. Python Virtual Environment Setup ---
echo "Setting up Python virtual environment..."
cd ${APP_DIR}
sudo -u azureuser python3 -m venv venv
source venv/bin/activate
sudo -u azureuser pip install -r requirements.txt

# --- 4. Log Directory Setup ---
echo "Setting up log directory /var/log/my_flask_app..."
sudo mkdir -p /var/log/my_flask_app
# Ensure the VMSS user (azureuser) can write to this directory
sudo chown -R azureuser:azureuser /var/log/my_flask_app
sudo chmod -R 755 /var/log/my_flask_app

# --- 5. Systemd Service File Setup ---
echo "Copying and enabling Systemd service file..."
# The service file will be copied by Terraform, ensure its paths are correct
SERVICE_FILE_SOURCE="${APP_DIR}/my_flask_app.service" # This file will be provided by Terraform via `file()`
SERVICE_FILE_DEST="/etc/systemd/system/my_flask_app.service"

# Ensure the service file points to the correct app directory
# This sed command assumes the original service file uses /opt/my_flask_app
sudo cp "${SERVICE_FILE_SOURCE}" "${SERVICE_FILE_DEST}"

# Enable the service to start on boot, but do NOT start it yet
# It will start when the VMSS instance boots up.
sudo systemctl daemon-reload
sudo systemctl enable my_flask_app.service

echo "Application setup complete. VM ready for generalization."
