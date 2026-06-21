import os
from datetime import datetime, timedelta, timezone

import boto3

cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
DISK_THRESHOLD = float(os.environ.get('DISK_THRESHOLD', '85'))
METRIC_NAMESPACE = os.environ.get('METRIC_NAMESPACE', 'CWAgent')
METRIC_NAME = os.environ.get('METRIC_NAME', 'disk_used_percent')


def lambda_handler(event, context):
  sns_topic_arn = event.get('sns_topic_arn') or SNS_TOPIC_ARN
  instance_ids = event.get('instance_ids') or []

  if not sns_topic_arn:
    return {'statusCode': 400, 'body': {'error': 'SNS_TOPIC_ARN is required'}}

  if not instance_ids:
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(
      Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    for reservation in response['Reservations']:
      for instance in reservation['Instances']:
        instance_ids.append(instance['InstanceId'])

  end_time = datetime.now(timezone.utc)
  start_time = end_time - timedelta(minutes=15)
  alerts = []

  for instance_id in instance_ids:
    response = cloudwatch.get_metric_statistics(
      Namespace=METRIC_NAMESPACE,
      MetricName=METRIC_NAME,
      Dimensions=[
        {'Name': 'InstanceId', 'Value': instance_id},
        {'Name': 'path', 'Value': '/'},
        {'Name': 'device', 'Value': 'xvda1'},
        {'Name': 'fstype', 'Value': 'xfs'},
      ],
      StartTime=start_time,
      EndTime=end_time,
      Period=900,
      Statistics=['Maximum'],
    )

    datapoints = response.get('Datapoints', [])
    if not datapoints:
      print(f'No disk metrics found for {instance_id}')
      continue

    utilization = max(point['Maximum'] for point in datapoints)
    print(f'Instance {instance_id} disk utilization: {utilization:.2f}%')

    if utilization > DISK_THRESHOLD:
      message = (
        f'Disk alert: instance {instance_id} disk utilization is '
        f'{utilization:.2f}% (threshold: {DISK_THRESHOLD}%)'
      )
      sns.publish(
        TopicArn=sns_topic_arn,
        Subject='EC2 Disk Space Alert',
        Message=message,
      )
      print(message)
      alerts.append({'instance_id': instance_id, 'utilization': utilization})

  return {
    'statusCode': 200,
    'body': {
      'alerts_sent': len(alerts),
      'alerts': alerts,
    },
  }
