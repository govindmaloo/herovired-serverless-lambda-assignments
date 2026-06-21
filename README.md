# AWS Serverless Lambda Assignments

HeroVired serverless assignments using AWS Lambda and Boto3. Each folder contains a `lambda_function.py` handler.

| # | Folder | Description |
|---|--------|-------------|
| 1 | `assignment-01-ec2-auto-stop-start` | Stop/start EC2 instances by `Action` tag |
| 2 | `assignment-02-s3-cleanup` | Delete S3 objects older than 30 days |
| 3 | `assignment-03-unencrypted-s3-monitor` | Detect S3 buckets without encryption |
| 4 | `assignment-04-ebs-snapshot-cleanup` | Create EBS snapshots and delete old ones |
| 5 | `assignment-05-ec2-auto-tagging` | Tag EC2 instances on launch via EventBridge |
| 6 | `assignment-06-billing-alert` | SNS alert when AWS billing exceeds threshold |
| 7 | `assignment-07-dynamodb-change-alert` | SNS alert on DynamoDB stream changes |
| 8 | `assignment-08-comprehend-sentiment` | Analyze review sentiment with Comprehend |
| 9 | `assignment-09-s3-to-glacier` | Archive old S3 objects to Glacier |
| 10 | `assignment-10-elb-5xx-alert` | SNS alert on ELB 5xx error spikes |
| 11 | `assignment-11-ec2-backup-cleanup` | Backup EC2 files to S3 and delete old backups |
| 12 | `assignment-12-ec2-autoscale` | Scale EC2 instances based on ELB load |
| 13 | `assignment-13-s3-public-audit` | Audit and alert on public S3 buckets |
| 14 | `assignment-14-ec2-state-monitor` | SNS alert on EC2 state changes |
| 15 | `assignment-15-s3-log-cleaner` | Delete S3 logs older than 90 days |
| 16 | `assignment-16-ec2-disk-alert` | SNS alert when disk utilization exceeds 85% |
| 17 | `assignment-17-restore-from-snapshot` | Restore EC2 instance from latest snapshot |
| 18 | `assignment-18-ec2-state-backup` | Save EC2 state to S3 before shutdown |
| 19 | `assignment-19-elb-health-checker` | SNS alert for unhealthy ELB targets |

Configure resource names (bucket, SNS topic, instance IDs, etc.) via Lambda environment variables or the test event payload.
