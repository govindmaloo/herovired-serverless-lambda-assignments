import boto3

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
  stopped_ids = []
  started_ids = []

  # Find running instances tagged Action=Auto-Stop and stop them
  stop_response = ec2.describe_instances(
    Filters=[
      {'Name': 'tag:Action', 'Values': ['Auto-Stop']},
      {'Name': 'instance-state-name', 'Values': ['running']},
    ]
  )

  for reservation in stop_response['Reservations']:
    for instance in reservation['Instances']:
      instance_id = instance['InstanceId']
      ec2.stop_instances(InstanceIds=[instance_id])
      stopped_ids.append(instance_id)
      print(f'Stopping instance: {instance_id}')

  # Find stopped instances tagged Action=Auto-Start and start them
  start_response = ec2.describe_instances(
    Filters=[
      {'Name': 'tag:Action', 'Values': ['Auto-Start']},
      {'Name': 'instance-state-name', 'Values': ['stopped']},
    ]
  )

  for reservation in start_response['Reservations']:
    for instance in reservation['Instances']:
      instance_id = instance['InstanceId']
      ec2.start_instances(InstanceIds=[instance_id])
      started_ids.append(instance_id)
      print(f'Starting instance: {instance_id}')

  print(f'Stopped instances: {stopped_ids}')
  print(f'Started instances: {started_ids}')

  return {
    'statusCode': 200,
    'body': {
      'stopped': stopped_ids,
      'started': started_ids,
    }
  }