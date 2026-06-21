# Assignment 1: Automated EC2 Stop/Start via Lambda

AWS Lambda function that stops EC2 instances tagged `Action=Auto-Stop` and starts instances tagged `Action=Auto-Start`.

## Structure

```
assignment-01-ec2-auto-stop-start/
├── lambda_function.py    # Lambda handler (Boto3)
└── docs/
    └── action.md         # Flow diagram and setup checklist
```

## Prerequisites

- Two EC2 instances tagged with key `Action` and values `Auto-Stop` / `Auto-Start`
- Lambda execution role with EC2 describe/stop/start permissions
- Python 3.x Lambda runtime

## Test

1. Ensure Auto-Stop instance is **running** and Auto-Start instance is **stopped**
2. Manually invoke the Lambda function
3. Verify states changed in EC2 console and CloudWatch logs

See `assignment-01-ec2-auto-stop-start/docs/action.md` for the full flow and checklist.
