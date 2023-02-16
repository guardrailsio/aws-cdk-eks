# aws-cdk-eks
Provision EKS cluster with AWS CDK

## Required tools

- npm (Node Package Manager)
- Python 3.7 or later including pip and virtualenv

### Install AWS CDK

Install the AWS CDK Toolkit globally using the following Node Package Manager command.

	npm install -g aws-cdk

Run the following command to verify correct installation and print the version number of the AWS CDK.

	cdk --version

### Bootstrap your AWS account

Deploying stacks with the AWS CDK requires dedicated Amazon S3 buckets and other containers to be available to AWS CloudFormation during deployment. Creating these is called bootstrapping. To bootstrap, issue:

	cdk bootstrap aws://ACCOUNT-NUMBER/REGION

### Install AWS CDK libraries for Python

	cd guardrails-on-eks
	python -m venv .venv
	source .venv/bin/activate
	pip install -r requirements.txt


## Deploy

Edit the file `app.py` and uncomment this line:

	#env=cdk.Environment(account='123456789012', region='us-east-1'),

Change `account='123456789012', region='us-east-1'` with your AWS account number and target region.

To generate and review the CloudFormation template, run:

	cdk synth

To create the CloudFormation stack and deploy the EKS cluster, run:

	cdk deploy

## Stack Custom Configuration

Most of the time, you may want to change the default configuration of the stack.
You can do it by adding your configuration to the `stack_config` dict object in `app.py`.
The default configuration is defined in `guardrails_on_eks/guardrails_on_eks_stack.py` start with `self.stack_config = {`

For further customization, you can change the code of `class GuardrailsOnEksStack` or even create your own stack. Please refer to [AWS CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/index.html).

### Options without default value
- eks_admin_iam_role: The IAM Role that will be mapped to `system:masters` user in Kubernetes RBAC. AWS user who can assume this IAM Role will be able to access EKS cluster as admin.

### Options with default value
- deploy_multi_az: boolean, choose between Multi-AZ or Single-AZ deployment
- vpc_cidr: string, VPC CIDR, this should be big enough to contain at least 1 /20 subnet and 1 /24 subnet per AZ
- vpc_max_azs: maximum number of AZs to use in target region
- eks_nodegroup_main_instance_type: instance type of EKS node group, recommended to be m5.large or bigger
- eks_nodegroup_main_disk_size: disk size of instances in EKS node group
- eks_nodegroup_main_min_size: minimum number of nodes in EKS node group
- eks_nodegroup_main_max_size: maximum number of nodes in EKS node group
- db_instance_type: instance type of RDS instance
- db_storage_size: disk size of RDS instance
- db_multi_az: boolean, deploy RDS instance with Multi-AZ or Single-AZ
