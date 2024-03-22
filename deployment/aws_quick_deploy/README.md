# Introduction

This repository contains scripts to create:
- One EC2 with Docker, Docker-Compose and the HubGPT application
- Security Groups
- Mounted Volume for ample storage
- Elastic IP

The scripts will create resources in: us-east-1 has been tested for now (N.B. to change this to ap-south-1 
will entail changing the AMI ID as well as there are different AMIs across regions)

# How to run it
- Make sure you are authenticated with the AWS CLI 
- EXPORT AWS_PROFILE=default # The name of the profile you want to use
- EXPORT STACK_NAME="name-for-your-stack"
- EXPORT AWS_REGION="region-code-here"

Then run:
- ./create-stack.sh

# How to clean up
- ./delete-stack.sh

# Cloud Formation

## EC2 User Guide
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/AWS_EC2.html

## EC2 Instance User Guide
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-ec2-instance.html

- AvailabilityZone
- ImageId
- InstanceType
- UserData

# Tips

## List profiles
 aws configure list-profiles

## Select profile
export AWS_PROFILE=user1

## Use a Profile for a specific aws command
--profile profile-name

## Make a sh file executable
sudo chmod +x filename.bin

## List all volumes on a machine
lsblk