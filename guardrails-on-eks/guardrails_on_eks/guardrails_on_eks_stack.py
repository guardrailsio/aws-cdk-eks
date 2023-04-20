from aws_cdk import Stack, CfnJson, CfnOutput, aws_ec2, aws_eks, aws_rds, aws_secretsmanager, aws_iam, aws_kms
from aws_cdk.lambda_layer_kubectl_v24 import KubectlV24Layer
from constructs import Construct

class GuardrailsOnEksStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, stack_config={}, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.stack_config = {
            "deploy_multi_az": True,
            "vpc_cidr": "172.31.0.0/16",
            "vpc_max_azs": 2,
            "eks_nodegroup_main_instance_type": "m5a.xlarge",
            "eks_nodegroup_main_disk_size": 50,
            "eks_nodegroup_main_max_size": 3,
            "eks_nodegroup_main_min_size": 3,
            "eks_admin_iam_role": "arn:aws:iam::changeme_aws_account_number:role/changeme_iam_role_name",
            "db_instance_type": "m5.large",
            "db_storage_size": 50,
            "db_multi_az": True,
        }

        try:
            self.stack_config.update(stack_config)
        except:
            pass

        if not self.stack_config["deploy_multi_az"]:
            self.stack_config["db_multi_az"] = False

        vpc = aws_ec2.Vpc(self, "GuardRailsVPC",
            ip_addresses=aws_ec2.IpAddresses.cidr(self.stack_config["vpc_cidr"]),
            subnet_configuration=[
                {"cidrMask": 24, "name": "ingress", "subnetType": aws_ec2.SubnetType.PUBLIC},
                {"cidrMask": 20, "name": "app", "subnetType": aws_ec2.SubnetType.PRIVATE_WITH_EGRESS}],
            max_azs=self.stack_config["vpc_max_azs"]
        )

        if not self.stack_config["deploy_multi_az"]:
            target_az = vpc.availability_zones[0]

        eks_encrypt_key = aws_kms.Key(self, "EKSEncryptKey", enable_key_rotation=True)
        eks = aws_eks.Cluster(self, "GuardRailsEKS",
            cluster_name="GuardRailsEKS",
            version=aws_eks.KubernetesVersion.V1_24,
            kubectl_layer=KubectlV24Layer(self, "kubectl"),
            vpc=vpc,
            vpc_subnets=[aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)],
            secrets_encryption_key=eks_encrypt_key,
            default_capacity=0
        )

        if self.stack_config["deploy_multi_az"]:
            eks_ng_subnets = aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)
        else:
            eks_ng_subnets = aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS, availability_zones=[target_az])

        eks_ng_main = eks.add_nodegroup_capacity("main",
            disk_size=self.stack_config["eks_nodegroup_main_disk_size"],
            instance_types=[aws_ec2.InstanceType(self.stack_config["eks_nodegroup_main_instance_type"])],
            max_size=self.stack_config["eks_nodegroup_main_max_size"],
            min_size=self.stack_config["eks_nodegroup_main_min_size"],
            subnets=eks_ng_subnets
        )

        # aws-auth config map
        admin_role = aws_iam.Role.from_role_arn(self, "AdminRole", self.stack_config["eks_admin_iam_role"])
        aws_auth = aws_eks.AwsAuth(self, "EKSAwsAuth", cluster=eks)
        aws_auth.add_role_mapping(admin_role, groups=["system:masters"], username="sso:admin")
        aws_auth.add_role_mapping(eks_ng_main.role, groups=["system:bootstrappers", "system:nodes"], username="system:node:{{EC2PrivateDNSName}}")

        # EKS add-ons
        aws_eks.CfnAddon(self, "EKSAddonVPCCNI",
            addon_name="vpc-cni",
            cluster_name=eks.cluster_name,
        )
        aws_eks.CfnAddon(self, "EKSAddonCoreDNS",
            addon_name="coredns",
            cluster_name=eks.cluster_name,
        )
        ebs_csi_role = aws_iam.Role(self, "EBSCSIRole",
            managed_policies=[aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEBSCSIDriverPolicy")],
            assumed_by=aws_iam.FederatedPrincipal(eks.open_id_connect_provider.open_id_connect_provider_arn,
                {
                    "StringEquals": CfnJson(self, "ConditionJson", value={
                        f"{eks.cluster_open_id_connect_issuer}:sub": "system:serviceaccount:kube-system:ebs-csi-controller-sa",
                        f"{eks.cluster_open_id_connect_issuer}:aud": "sts.amazonaws.com"
                    })
                },
                "sts:AssumeRoleWithWebIdentity"),
        )
        aws_eks.CfnAddon(self, "EKSAddonCSIDriver",
            addon_name="aws-ebs-csi-driver",
            cluster_name=eks.cluster_name,
            service_account_role_arn=ebs_csi_role.role_arn,
        )


        db_sg = aws_ec2.SecurityGroup(self, "DatabaseSecurityGroup", vpc=vpc)
        db_sg.add_egress_rule(
            peer=aws_ec2.Peer.any_ipv4(),
            connection=aws_ec2.Port.all_traffic(),
            description="Allow all outbound traffic by default"
        )
        db_sg.add_ingress_rule(
            peer=aws_ec2.Peer.ipv4(self.stack_config["vpc_cidr"]),
            connection=aws_ec2.Port.tcp(5432),
            description="Allow connection to Postgres port within VPC"
        )

        if not self.stack_config["deploy_multi_az"]:
            db_az = target_az
        else:
            db_az = None

        db = aws_rds.DatabaseInstance(
            self, "Database",
            engine=aws_rds.DatabaseInstanceEngine.postgres(version=aws_rds.PostgresEngineVersion.VER_12_9),
            credentials=aws_rds.Credentials.from_generated_secret("guardrails"),
            vpc=vpc,
            multi_az=self.stack_config["db_multi_az"],
            instance_type=aws_ec2.InstanceType(self.stack_config["db_instance_type"]),
            allocated_storage=self.stack_config["db_storage_size"],
            storage_encrypted=True,
            security_groups=[db_sg],
            availability_zone=db_az
        )

        CfnOutput(self, "EKSClusterName", value=eks.cluster_name)
        CfnOutput(self, "RDSInstanceEndpoint", value=db.instance_endpoint.socket_address)
        CfnOutput(self, "RDSGetCredentialSecretCommand", value=f"aws secretsmanager get-secret-value --secret-id {db.secret.secret_name}")
