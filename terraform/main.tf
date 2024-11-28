
    provider "aws" {
      region = "ap-south-1"
    }

    resource "aws_instance" "primary" {
      ami           = "ami-0dee22c13ea7a9a67"
      instance_type = "t2.micro"
      tags = { Name = "postgres-primary" }
    }

    
    resource "aws_instance" "replica_0" {
      ami           = "ami-0dee22c13ea7a9a67"
      instance_type = "t2.micro"
      tags = { Name = "postgres-replica-0" }
    }
    
    resource "aws_instance" "replica_1" {
      ami           = "ami-0dee22c13ea7a9a67"
      instance_type = "t2.micro"
      tags = { Name = "postgres-replica-1" }
    }
    
    