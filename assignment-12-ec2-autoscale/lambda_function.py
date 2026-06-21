import os
from datetime import datetime, timedelta, timezone

import boto3

cloudwatch = boto3.client('cloudwatch')
ec2 = boto3.client('ec2')
sns = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
LOAD_BALANCER = os.environ.get('LOAD_BALANCER')
HIGH_THRESHOLD = float(os.environ.get('HIGH_THRESHOLD', '80'))
LOW_THRESHOLD = float(os.environ.get('LOW_THRESHOLD', '20'))
AMI_ID = os.environ.get('AMI_ID')
INSTANCE_TYPE = os.environ.get('INSTANCE_TYPE', 't2.micro')
SUBNET_ID = os.environ.get('SUBNET_ID')
SECURITY_GROUP_ID = os.environ.get('SECURITY_GROUP_ID')
SCALE_TAG_KEY = os.environ.get('SCALE_TAG_KEY', 'AutoScale')
SCALE_TAG_VALUE = os.environ.get('SCALE_TAG_VALUE', 'Managed')


def get_network_load(load_balancer):
  end_time = datetime.now(timezone.utc)
  start_time = end_time - timedelta(minutes=5)

  response = cloudwatch.get_metric_statistics(
    Namespace='AWS/ApplicationELB',
    MetricName='ProcessedBytes',
    Dimensions=[{'Name': 'LoadBalancer', 'Value': load_balancer}],
    StartTime=start_time,
    EndTime=end_time,
    Period=300,
    Statistics=['Average'],
  )

  datapoints = response.get('Datapoints', [])
  if not datapoints:
    return 0.0

  return max(point['Average'] for point in datapoints)


def get_scaled_instances():
  response = ec2.describe_instances(
    Filters=[
      {'Name': f'tag:{SCALE_TAG_KEY}', 'Values': [SCALE_TAG_VALUE]},
      {'Name': 'instance-state-name', 'Values': ['pending', 'running']},
    ]
  )

  instance_ids = []
  for reservation in response['Reservations']:
    for instance in reservation['Instances']:
      instance_ids.append(instance['InstanceId'])
  return instance_ids


def lambda_handler(event, context):
  load_balancer = event.get('load_balancer') or LOAD_BALANCER
  sns_topic_arn = event.get('sns_topic_arn') or SNS_TOPIC_ARN

  if not load_balancer or not sns_topic_arn:
    return {
      'statusCode': 400,
      'body': {'error': 'load_balancer and SNS_TOPIC_ARN are required'},
    }

  load = get_network_load(load_balancer)
  print(f'Network load metric: {load}')

  action = 'none'
  target_instance_id = None

  if load > HIGH_THRESHOLD:
    if not all([AMI_ID, SUBNET_ID, SECURITY_GROUP_ID]):
      return {
        'statusCode': 400,
        'body': {'error': 'AMI_ID, SUBNET_ID, and SECURITY_GROUP_ID are required to scale up'},
      }

    instance = ec2.run_instances(
      ImageId=AMI_ID,
      InstanceType=INSTANCE_TYPE,
      MinCount=1,
      MaxCount=1,
      SubnetId=SUBNET_ID,
      SecurityGroupIds=[SECURITY_GROUP_ID],
      TagSpecifications=[{
        'ResourceType': 'instance',
        'Tags': [{'Key': SCALE_TAG_KEY, 'Value': SCALE_TAG_VALUE}],
      }],
    )['Instances'][0]
    target_instance_id = instance['InstanceId']
    action = 'scale_up'
    message = f'Scaled up: launched instance {target_instance_id} due to high load ({load})'

  elif load < LOW_THRESHOLD:
    instances = get_scaled_instances()
    if instances:
      target_instance_id = instances[0]
      ec2.terminate_instances(InstanceIds=[target_instance_id])
      action = 'scale_down'
      message = f'Scaled down: terminated instance {target_instance_id} due to low load ({load})'
    else:
      message = f'Load is low ({load}) but no managed instances available to terminate'
  else:
    message = f'Load {load} is within thresholds; no scaling action taken'

  sns.publish(
    TopicArn=sns_topic_arn,
    Subject='EC2 Auto-Scale Notification',
    Message=message,
  )
  print(message)

  return {
    'statusCode': 200,
    'body': {
      'action': action,
      'load': load,
      'instance_id': target_instance_id,
      'message': message,
    },
  }
