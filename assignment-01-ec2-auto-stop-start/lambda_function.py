import boto3

ec2 = boto3.client('ec2')

TAG_KEY = 'Action'

def get_instances_by_tag(tag_value):
  response = ec2.describe_instances(
    Filters=[{'Name': f'tag:{TAG_KEY}', 'Values': [tag_value]}]
  )

  instances = []
  for reservation in response['Reservations']:
    instances.extend(reservation['Instances'])
  return instances


def lambda_handler(event, context):
  stopped_ids = []
  started_ids = []

  # Step 1: find instances by tag only, then stop running Auto-Stop instances
  for instance in get_instances_by_tag('Auto-Stop'):
    instance_id = instance['InstanceId']
    state = instance['State']['Name']
    print(f'Found Auto-Stop instance: {instance_id} (state: {state})')

    if state == 'running':
      ec2.stop_instances(InstanceIds=[instance_id])
      stopped_ids.append(instance_id)
      print(f'Stopping instance: {instance_id}')

  # Step 2: find instances by tag only, then start stopped Auto-Start instances
  for instance in get_instances_by_tag('Auto-Start'):
    instance_id = instance['InstanceId']
    state = instance['State']['Name']
    print(f'Found Auto-Start instance: {instance_id} (state: {state})')

    if state == 'stopped':
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