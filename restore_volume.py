import boto3
from operator import itemgetter

ec2_client = boto3.client('ec2', region_name="us-east-1")
ec2_resource = boto3.resource('ec2', region_name="us-east-1")

# Fetch the VOLUMES of the given EC2 Instance
instance_id = "replace-with-your-instance-id" # CHANGE EC2 INSTANCE ID !!!!!!!!!!!
volumes = ec2_client.describe_volumes(
	Filters=[
		{
			'Name': 'attachment.instance-id',
			'Values': [instance_id]
		}
	]
)

# Assigns the first volume to the variable 'instance_volume'
instance_volume = volumes['Volumes'][0]

# Fetch the SNAPSHOTS of the given Volume
snapshots = ec2_client.describe_snapshots(
    OwnerIds=['self'],
    Filters=[
        {
            'Name': 'volume-id',
            'Values': [instance_volume['VolumeId']]
        }
    ]
)

# Sort snapshots by time, with the latest at position [0]
latest_snapshot = sorted(
    snapshots['Snapshots'],
    key=itemgetter('StartTime'),
    reverse=True)[0]
print(latest_snapshot['StartTime'])

# Create new volume from fetched snapshot
new_volume = ec2_client.create_volume(
    SnapshotId=latest_snapshot['SnapshotId'],
    AvailabilityZone="replace-with-your-aws-zone", # CHANGE ZONE !!!!!!!!!!!
    TagSpecifications=[
        {
            'ResourceType': 'volume',
            'Tags':[
                {
                    'Key': 'Name',
                    'Value': 'prod'
                }
            ]
        }
    ]
)

# Loop to check for 'available' state of new volume
while True:
    vol = ec2_resource.Volume(new_volume['VolumeId'])
    print(vol.state)
    if vol.state == 'available':
        # Attach new volume to EC2 Instance
        ec2_resource.Instance(instance_id).attach_volume(
            VolumeId=new_volume['VolumeId'],
            Device='/dev/xvdb',
        )
        break