# CloudWatch Integration Testing Plan

This document outlines the procedure for testing the CloudWatch integration to ensure that logs and metrics are correctly delivered and alarms function as expected.

## Prerequisites

- AWS account with the application deployed
- AWS CLI configured with appropriate credentials
- SSH access to the EC2 instance
- Access to the AWS Management Console

## Test 1: Log Delivery

### Objective
Verify that application logs are successfully delivered to CloudWatch Logs.

### Steps

1. Generate application logs by using the application:
   ```bash
   # Login to get an access token
   curl -X 'POST' 'http://<EC2_IP>/login/access-token' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'username=admin@example.com&password=admin'

   # Use the token to list files (generates logs)
   curl -X 'GET' 'http://<EC2_IP>/api/v1/files' \
     -H "Authorization: Bearer <ACCESS_TOKEN>"
   ```

2. Check CloudWatch Logs:
   ```bash
   # Using AWS CLI
   aws logs get-log-events \
     --log-group-name "/aws/ec2/we-upload" \
     --log-stream-name "<INSTANCE_ID>/app.log" \
     --limit 10
   ```

3. Alternatively, check logs in the AWS Management Console:
   - Navigate to CloudWatch > Log groups > /aws/ec2/we-upload
   - Select the log stream for the EC2 instance
   - Verify that logs are in structured JSON format

### Expected Result
- Logs should appear in CloudWatch within a few minutes
- Log entries should be in JSON format and include all required fields
- No errors should be reported in the CloudWatch agent logs

## Test 2: Metrics Collection

### Objective
Verify that custom metrics are collected and displayed in CloudWatch.

### Steps

1. Generate load on the system:
   ```bash
   # Create a simple load test using curl
   for i in {1..50}; do
     curl -s "http://<EC2_IP>/health" > /dev/null
     sleep 0.5
   done
   ```

2. Check CloudWatch Metrics:
   ```bash
   # Using AWS CLI
   aws cloudwatch get-metric-statistics \
     --namespace "CWAgent" \
     --metric-name "mem_used_percent" \
     --dimensions Name=InstanceId,Value=<INSTANCE_ID> \
     --start-time $(date -u -v-1H +"%Y-%m-%dT%H:%M:%SZ") \
     --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ") \
     --period 300 \
     --statistics Average
   ```

3. Also check in the AWS Management Console:
   - Navigate to CloudWatch > Metrics > All metrics
   - Select "CWAgent" namespace
   - Check "mem_used_percent" and "disk_used_percent" metrics

### Expected Result
- Memory and disk usage metrics should be visible
- Metrics should update at the configured interval (60 seconds)
- No gaps should be present in the metrics data

## Test 3: Alarm Functionality

### Objective
Verify that alarms trigger correctly when thresholds are exceeded.

### Steps

1. Temporarily lower the CPU alarm threshold:
   ```bash
   # Using AWS CLI
   aws cloudwatch put-metric-alarm \
     --alarm-name "we-upload-cpu-utilization-high" \
     --alarm-description "This metric monitors EC2 CPU utilization" \
     --metric-name "CPUUtilization" \
     --namespace "AWS/EC2" \
     --statistic "Average" \
     --period 60 \
     --evaluation-periods 2 \
     --threshold 10 \
     --comparison-operator "GreaterThanThreshold" \
     --dimensions Name=InstanceId,Value=<INSTANCE_ID>
   ```

2. Generate CPU load on the EC2 instance:
   ```bash
   # SSH into the EC2 instance
   ssh -i <KEY_FILE> ubuntu@<EC2_IP>

   # Generate CPU load
   dd if=/dev/zero of=/dev/null bs=1M count=1000
   ```

3. Check if alarm was triggered:
   ```bash
   # Using AWS CLI
   aws cloudwatch describe-alarms \
     --alarm-names "we-upload-cpu-utilization-high"
   ```

4. Restore original alarm threshold:
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name "we-upload-cpu-utilization-high" \
     --alarm-description "This metric monitors EC2 CPU utilization" \
     --metric-name "CPUUtilization" \
     --namespace "AWS/EC2" \
     --statistic "Average" \
     --period 300 \
     --evaluation-periods 2 \
     --threshold 80 \
     --comparison-operator "GreaterThanThreshold" \
     --dimensions Name=InstanceId,Value=<INSTANCE_ID>
   ```

### Expected Result
- The alarm should change to the "ALARM" state when CPU usage exceeds the threshold
- The alarm should return to the "OK" state when CPU usage drops below the threshold

## Test 4: Log Retention

### Objective
Verify that log retention policies are correctly applied.

### Steps

1. Check the log retention setting:
   ```bash
   # Using AWS CLI
   aws logs describe-log-groups \
     --log-group-name-prefix "/aws/ec2/we-upload"
   ```

2. Verify it matches the configured value (7 days)

### Expected Result
- The log group should have a retention policy of 7 days
- No extra log groups should be created
- The retention setting should match what was defined in Terraform

## Test 5: Dashboard Display

### Objective
Verify that metrics are correctly displayed in the CloudWatch dashboard.

### Steps

1. Create a simple dashboard for monitoring:
   ```bash
   # Using AWS CLI (with a minimal dashboard configuration)
   aws cloudwatch put-dashboard \
     --dashboard-name "we-upload-monitoring" \
     --dashboard-body '{
       "widgets": [
         {
           "type": "metric",
           "x": 0,
           "y": 0,
           "width": 12,
           "height": 6,
           "properties": {
             "metrics": [
               [ "AWS/EC2", "CPUUtilization", "InstanceId", "<INSTANCE_ID>" ],
               [ "CWAgent", "mem_used_percent", "InstanceId", "<INSTANCE_ID>" ],
               [ "CWAgent", "disk_used_percent", "InstanceId", "<INSTANCE_ID>", "path", "/", "fstype", "xfs" ]
             ],
             "period": 300,
             "stat": "Average",
             "region": "<REGION>",
             "title": "We-Upload System Metrics"
           }
         }
       ]
     }'
   ```

2. Check the dashboard in the AWS Management Console:
   - Navigate to CloudWatch > Dashboards > we-upload-monitoring

### Expected Result
- The dashboard should display all configured metrics
- Graphs should show data for CPU, memory, and disk usage
- The dashboard should update in real-time (within CloudWatch's refresh interval)

## Troubleshooting

If tests fail, check these common issues:

1. **CloudWatch Agent Installation**
   - Verify agent is installed: `dpkg -l | grep amazon-cloudwatch-agent`
   - Check agent status: `systemctl status amazon-cloudwatch-agent`
   - Check agent logs: `cat /var/log/amazon/amazon-cloudwatch-agent/amazon-cloudwatch-agent.log`

2. **IAM Permissions**
   - Verify EC2 instance has the CloudWatchAgentServerPolicy attached
   - Check instance profile: `aws ec2 describe-iam-instance-profile-associations`

3. **Configuration Issues**
   - Verify CloudWatch agent config file: `cat /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json`
   - Make sure paths and log group names are correct
   - Check that logs directory exists: `ls -la /app/logs`

4. **Network Issues**
   - Ensure EC2 instance has outbound internet access
   - Verify security groups allow outbound traffic to AWS APIs
