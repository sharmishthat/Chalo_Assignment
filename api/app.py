from flask import Flask, request, jsonify
from jinja2 import Template
import os
import subprocess
import json

app = Flask(__name__)

AWS_REGION = "ap-south-1"
AMI_ID = "ami-0dee22c13ea7a9a67"  # Replace this with the correct AMI ID for ap-south-1

# Helper function to get Terraform outputs
def get_terraform_outputs():
    try:
        env = os.environ.copy()
        env["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID")
        env["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY")

        os.chdir("../terraform")
        result = subprocess.run(["terraform", "output", "-json"], capture_output=True, text=True, env=env, check=True)
        os.chdir("../api")
        outputs = json.loads(result.stdout)
        return {
            "primary_ips": outputs.get("instance_ips", {}).get("value", []),
            "replica_ips": outputs.get("replica_ips", {}).get("value", [])
        }
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@app.route('/generate', methods=['POST'])
def generate_configs():
    data = request.json
    postgres_version = data['postgresVersion']
    instance_type = data['instanceType']
    num_replicas = data['numReplicas']
    settings = data['settings']

    # Generate Terraform configuration
    terraform_template = """
    provider "aws" {
      region = "{{ region }}"
    }

    resource "aws_instance" "primary" {
      ami           = "{{ ami_id }}"
      instance_type = "{{ instance_type }}"
      tags = { Name = "postgres-primary" }
    }

    {% for i in range(num_replicas) %}
    resource "aws_instance" "replica_{{ i }}" {
      ami           = "{{ ami_id }}"
      instance_type = "{{ instance_type }}"
      tags = { Name = "postgres-replica-{{ i }}" }
    }
    {% endfor %}

    output "instance_ips" {
      value = [aws_instance.primary.public_ip]
    }

    output "replica_ips" {
      value = [ {% for i in range(num_replicas) %} aws_instance.replica_{{ i }}.public_ip {% if not loop.last %}, {% endif %} {% endfor %} ]
    }
    """

    terraform_config = Template(terraform_template).render(
        region=AWS_REGION, ami_id=AMI_ID, instance_type=instance_type, num_replicas=num_replicas
    )
    os.makedirs("../terraform", exist_ok=True)
    with open("../terraform/main.tf", "w") as tf_file:
        tf_file.write(terraform_config)

    # Generate Ansible Playbook
    ansible_template = """
    - name: Configure PostgreSQL
      hosts: all
      become: yes
      tasks:
        - name: Install PostgreSQL
          apt:
            name: postgresql-{{ postgres_version }}
            state: present

        - name: Set max_connections
          lineinfile:
            path: /etc/postgresql/{{ postgres_version }}/main/postgresql.conf
            regexp: '^max_connections'
            line: "max_connections = {{ settings['maxConnections'] }}"
            state: present

        - name: Set shared_buffers
          lineinfile:
            path: /etc/postgresql/{{ postgres_version }}/main/postgresql.conf
            regexp: '^shared_buffers'
            line: "shared_buffers = {{ settings['sharedBuffers'] }}"
            state: present
    """

    ansible_config = Template(ansible_template).render(
        postgres_version=postgres_version, settings=settings
    )
    os.makedirs("../ansible", exist_ok=True)
    with open("../ansible/playbook.yml", "w") as ansible_file:
        ansible_file.write(ansible_config)

    return jsonify({"message": "Terraform and Ansible configurations generated successfully!"})

@app.route('/terraform/apply', methods=['POST'])
def terraform_apply():
    try:
        env = os.environ.copy()
        env["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID")
        env["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY")

        os.chdir("../terraform")
        subprocess.run(["terraform", "init"], check=True, env=env)
        subprocess.run(["terraform", "apply", "-auto-approve"], check=True, env=env)
        os.chdir("../api")
        return jsonify({"message": "Terraform applied successfully!"})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)})

@app.route('/ansible/generate', methods=['POST'])
def generate_ansible_inventory():
    terraform_outputs = get_terraform_outputs()
    if "error" in terraform_outputs:
        return jsonify({"error": terraform_outputs["error"]})

    primary_ips = terraform_outputs["primary_ips"]
    replica_ips = terraform_outputs["replica_ips"]

    inventory_template = """
    [primary]
    {% for ip in primary_ips %}
    {{ ip }}
    {% endfor %}

    [replicas]
    {% for ip in replica_ips %}
    {{ ip }}
    {% endfor %}
    """

    inventory_content = Template(inventory_template).render(
        primary_ips=primary_ips, replica_ips=replica_ips
    )

    os.makedirs("../ansible", exist_ok=True)
    with open("../ansible/hosts", "w") as inventory_file:
        inventory_file.write(inventory_content)

    return jsonify({"message": "Ansible inventory generated successfully!"})

@app.route('/ansible/run', methods=['POST'])
def ansible_run():
    try:
        subprocess.run(
            ["ansible-playbook", "../ansible/playbook.yml", "-i", "../ansible/hosts"],
            check=True
        )
        return jsonify({"message": "Ansible playbook executed successfully!"})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

