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
