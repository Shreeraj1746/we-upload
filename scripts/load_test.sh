#!/bin/bash

# Get the EC2 IP from the Terraform output
EC2_IP=$(terraform output | grep 'ec2_instance_public_ip =' | sed 's/.*= "\([0-9\.]*\)".*/\1/' | head -n 1 | tr -d '\n' | tr -d ' ')
echo "EC2 IP: $EC2_IP"

# Create a simple load test using curl
for i in {1..50}; do
  echo "Request $i: http://$EC2_IP/health"
  curl -s "http://$EC2_IP/health" > /dev/null
  sleep 0.5
done
