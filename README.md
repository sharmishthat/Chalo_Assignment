# Terraform and Ansible Automation for PostgreSQL Deployment

This repository automates the deployment of a PostgreSQL cluster on AWS using Terraform and Ansible. The Flask application generates configuration files dynamically and manages the deployment.

## Features

- Deploy PostgreSQL with replicas on AWS using Terraform.
- Configure PostgreSQL settings using Ansible playbooks.
- Automatically generate inventory files from Terraform outputs.

## Prerequisites

- Python 3.x
- Terraform
- Ansible
- AWS Credentials (Access Key and Secret Key)

## Setup

1. Clone the repository:
   git clone <repository-url>
   cd project
2. pip install -r api/requirements.txt
3. export AWS_ACCESS_KEY_ID="your-access-key"
   export AWS_SECRET_ACCESS_KEY="your-secret-key"

## Usage
1. Start the Flask Application
Run the Flask app to start the API:

python3 app.py
The app will be accessible at http://0.0.0.0:5000.

2. Generate Configurations
Send a POST request to generate Terraform and Ansible configurations:

curl -X POST -H "Content-Type: application/json" -d '{
    "postgresVersion": 13,
    "instanceType": "t2.micro",
    "numReplicas": 2,
    "settings": {
        "maxConnections": 100,
        "sharedBuffers": "128MB"
    }
}' http://localhost:5000/generate

3. Apply Terraform
Deploy instances using Terraform:

curl -X POST http://localhost:5000/terraform/apply

4. Generate Ansible Inventory
Generate the Ansible inventory file:

curl -X POST http://localhost:5000/ansible/generate

5. Run Ansible Playbook
Configure PostgreSQL on the deployed instances:

curl -X POST http://localhost:5000/ansible/run

File Structure
plaintext
Copy code
project/
├── api/
│   ├── app.py               # Flask app for Terraform and Ansible
│   ├── requirements.txt     # Python dependencies
├── terraform/               # Terraform configuration (will be generated)
├── ansible/                 # Ansible playbooks and inventory (will be generated)
├── .gitignore               # To ignore unnecessary files in Git
├── README.md                # Documentation for the repository
