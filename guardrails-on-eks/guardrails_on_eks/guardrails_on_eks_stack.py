from aws_cdk import Stack, aws_ec2, aws_eks, aws_rds, aws_secretsmanager
from aws_cdk.lambda_layer_kubectl_v24 import KubectlV24Layer
from constructs import Construct
import json

class GuardrailsOnEksStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, stack_config={}, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.stack_config = {
            "vpc_cidr": "172.31.0.0/16",
            "vpc_max_azs": 2,
            "eks_nodegroup_main_instance_type": "m5a.xlarge",
            "eks_nodegroup_main_disk_size": 50,
            "eks_nodegroup_main_max_size": 3,
            "eks_nodegroup_main_min_size": 3,
            "db_instance_type": "m5.large",
            "db_storage_size": 50,
            "db_multi_az": True,
        }

        try:
            self.stack_config.update(stack_config)
        except:
            pass

        vpc = aws_ec2.Vpc(self, "GuardRailsVPC",
            ip_addresses=aws_ec2.IpAddresses.cidr(self.stack_config["vpc_cidr"]),
            subnet_configuration=[
                {"cidrMask": 24, "name": "ingress", "subnetType": aws_ec2.SubnetType.PUBLIC},
                {"cidrMask": 20, "name": "app", "subnetType": aws_ec2.SubnetType.PRIVATE_WITH_EGRESS}],
            max_azs=self.stack_config["vpc_max_azs"]
        )

        eks = aws_eks.Cluster(self, "GuardRailsEKS",
            version=aws_eks.KubernetesVersion.V1_24,
            kubectl_layer=KubectlV24Layer(self, "kubectl"),
            vpc=vpc,
            vpc_subnets=[aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)],
            default_capacity=0
        )

        eks.add_nodegroup_capacity("main",
            disk_size=self.stack_config["eks_nodegroup_main_disk_size"],
            instance_types=[aws_ec2.InstanceType(self.stack_config["eks_nodegroup_main_instance_type"])],
            max_size=self.stack_config["eks_nodegroup_main_max_size"],
            min_size=self.stack_config["eks_nodegroup_main_min_size"]
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

        db = aws_rds.DatabaseInstance(
            self, "Database",
            engine=aws_rds.DatabaseInstanceEngine.postgres(version=aws_rds.PostgresEngineVersion.VER_12_9),
            credentials=aws_rds.Credentials.from_generated_secret("postgres"),
            vpc=vpc,
            multi_az=self.stack_config["db_multi_az"],
            instance_type=aws_ec2.InstanceType(self.stack_config["db_instance_type"]),
            allocated_storage=self.stack_config["db_storage_size"],
            storage_encrypted=True,
            security_groups=[db_sg]
        )
