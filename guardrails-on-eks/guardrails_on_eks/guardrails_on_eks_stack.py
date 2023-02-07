from aws_cdk import Stack, aws_ec2, aws_eks, aws_rds, aws_secretsmanager
from aws_cdk.lambda_layer_kubectl_v24 import KubectlV24Layer
from constructs import Construct
import json

class GuardrailsOnEksStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc_cidr = "172.31.0.0/16"
        vpc = aws_ec2.Vpc(self, "GuardRailsVPC",
            ip_addresses=aws_ec2.IpAddresses.cidr(vpc_cidr),
            subnet_configuration=[
                {"cidrMask": 24, "name": "ingress", "subnetType": aws_ec2.SubnetType.PUBLIC},
                {"cidrMask": 20, "name": "app", "subnetType": aws_ec2.SubnetType.PRIVATE_WITH_EGRESS}],
            max_azs=2
        )

        eks = aws_eks.Cluster(self, "GuardRailsEKS",
            version=aws_eks.KubernetesVersion.V1_24,
            kubectl_layer=KubectlV24Layer(self, "kubectl"),
            vpc=vpc,
            vpc_subnets=[aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)]
        )

        eks.add_nodegroup_capacity("main",
            disk_size=50,
            instance_types=[aws_ec2.InstanceType("m5a.large")],
            max_size=3,
            min_size=3
        )

        db_sg = aws_ec2.SecurityGroup(self, "DatabaseSecurityGroup", vpc=vpc)
        db_sg.add_egress_rule(
            peer=aws_ec2.Peer.any_ipv4(),
            connection=aws_ec2.Port.all_traffic(),
            description="Allow all outbound traffic by default"
        )
        db_sg.add_ingress_rule(
            peer=aws_ec2.Peer.ipv4(vpc_cidr),
            connection=aws_ec2.Port.tcp(5432),
            description="Allow connection to Postgres port within VPC"
        )

        db = aws_rds.DatabaseInstance(
            self, "Database",
            engine=aws_rds.DatabaseInstanceEngine.postgres(version=aws_rds.PostgresEngineVersion.VER_12_9),
            credentials=aws_rds.Credentials.from_generated_secret("postgres"),
            vpc=vpc,
            multi_az=True,
            instance_type=aws_ec2.InstanceType("m5.large"),
            allocated_storage=50,
            storage_encrypted=True,
            security_groups=[db_sg]
        )
