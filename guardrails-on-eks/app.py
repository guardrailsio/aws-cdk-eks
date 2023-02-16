#!/usr/bin/env python3
import os

import aws_cdk as cdk

from guardrails_on_eks.guardrails_on_eks_stack import GuardrailsOnEksStack


app = cdk.App()
GuardrailsOnEksStack(app, "GuardrailsOnEksStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),
    stack_config = {
        "deploy_multi_az": True,
        "eks_nodegroup_main_max_size": 4,
        "eks_nodegroup_main_min_size": 2,
        "eks_admin_iam_role": "arn:aws:iam::changeme_aws_account_number:role/changeme_iam_role_name",
    }

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

app.synth()
