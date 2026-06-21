import os

import boto3

ec2 = boto3.client('ec2')

INSTANCE_TYPE = os.environ.get('INSTANCE_TYPE', 't2.micro')
SUBNET_ID = os.environ.get('SUBNET_ID')
SECURITY_GROUP_ID = os.environ.get('SECURITY_GROUP_ID')


def lambda_handler(event, context):
  instance_id = event.get('instance_id') or os.environ.get('INSTANCE_ID')
  if not instance_id:
    return {'statusCode': 400, 'body': {'error': 'instance_id is required'}}

  reservations = ec2.describe_instances(InstanceIds=[instance_id])['Reservations']
  if not reservations:
    return {'statusCode': 404, 'body': {'error': f'Instance {instance_id} not found'}}

  instance = reservations[0]['Instances'][0]
  volume_ids = [
    mapping['Ebs']['VolumeId']
    for mapping in instance.get('BlockDeviceMappings', [])
    if 'Ebs' in mapping
  ]

  if not volume_ids:
    return {'statusCode': 400, 'body': {'error': 'No EBS volumes found for instance'}}

  snapshots = ec2.describe_snapshots(
    Filters=[{'Name': 'volume-id', 'Values': volume_ids}],
    OwnerIds=['self'],
  )['Snapshots']

  if not snapshots:
    return {'statusCode': 404, 'body': {'error': 'No snapshots found for instance volumes'}}

  latest_snapshot = sorted(snapshots, key=lambda item: item['StartTime'], reverse=True)[0]
  snapshot_id = latest_snapshot['SnapshotId']
  print(f'Using latest snapshot: {snapshot_id}')

  if not SUBNET_ID or not SECURITY_GROUP_ID:
    return {
      'statusCode': 400,
      'body': {
        'error': 'SUBNET_ID and SECURITY_GROUP_ID are required to launch restored instance',
        'snapshot_id': snapshot_id,
      },
    }

  volume = ec2.create_volume(
    SnapshotId=snapshot_id,
    AvailabilityZone=instance['Placement']['AvailabilityZone'],
  )
  volume_id = volume['VolumeId']
  ec2.get_waiter('volume_available').wait(VolumeIds=[volume_id])

  new_instance = ec2.run_instances(
    ImageId=instance['ImageId'],
    InstanceType=INSTANCE_TYPE,
    MinCount=1,
    MaxCount=1,
    SubnetId=SUBNET_ID,
    SecurityGroupIds=[SECURITY_GROUP_ID],
    BlockDeviceMappings=[{
      'DeviceName': instance['RootDeviceName'],
      'Ebs': {'VolumeId': volume_id, 'DeleteOnTermination': True},
    }],
  )['Instances'][0]

  new_instance_id = new_instance['InstanceId']
  print(f'Created instance {new_instance_id} from snapshot {snapshot_id}')

  return {
    'statusCode': 200,
    'body': {
      'source_instance_id': instance_id,
      'snapshot_id': snapshot_id,
      'new_instance_id': new_instance_id,
      'volume_id': volume_id,
    },
  }
