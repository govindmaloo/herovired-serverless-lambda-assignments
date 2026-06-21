import os
from datetime import datetime, timedelta, timezone

import boto3

cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
LOAD_BALANCER = os.environ.get('LOAD_BALANCER')
ERROR_THRESHOLD = int(os.environ.get('ERROR_THRESHOLD', '10'))
METRIC_NAMESPACE = os.environ.get('METRIC_NAMESPACE', 'AWS/ApplicationELB')
METRIC_NAME = os.environ.get('METRIC_NAME', 'HTTPCode_Target_5XX_Count')


def lambda_handler(event, context):
  load_balancer = event.get('load_balancer') or LOAD_BALANCER
  sns_topic_arn = event.get('sns_topic_arn') or SNS_TOPIC_ARN

  if not load_balancer or not sns_topic_arn:
    return {
      'statusCode': 400,
      'body': {'error': 'load_balancer and SNS_TOPIC_ARN are required'},
    }

  end_time = datetime.now(timezone.utc)
  start_time = end_time - timedelta(minutes=5)

  response = cloudwatch.get_metric_statistics(
    Namespace=METRIC_NAMESPACE,
    MetricName=METRIC_NAME,
    Dimensions=[{'Name': 'LoadBalancer', 'Value': load_balancer}],
    StartTime=start_time,
    EndTime=end_time,
    Period=300,
    Statistics=['Sum'],
  )

  datapoints = response.get('Datapoints', [])
  error_count = int(sum(point.get('Sum', 0) for point in datapoints))
  print(f'5xx errors in last 5 minutes: {error_count}')

  if error_count > ERROR_THRESHOLD:
    message = (
      f'ELB 5xx alert: {error_count} errors detected on {load_balancer} '
      f'in the last 5 minutes (threshold: {ERROR_THRESHOLD})'
    )
    sns.publish(
      TopicArn=sns_topic_arn,
      Subject='ELB 5xx Error Spike',
      Message=message,
    )
    print(message)
    return {
      'statusCode': 200,
      'body': {'alert_sent': True, 'error_count': error_count},
    }

  return {
    'statusCode': 200,
    'body': {'alert_sent': False, 'error_count': error_count},
  }
