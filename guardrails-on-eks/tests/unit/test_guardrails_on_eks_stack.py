import aws_cdk as core
import aws_cdk.assertions as assertions

from guardrails_on_eks.guardrails_on_eks_stack import GuardrailsOnEksStack

# example tests. To run these tests, uncomment this file along with the example
# resource in guardrails_on_eks/guardrails_on_eks_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = GuardrailsOnEksStack(app, "guardrails-on-eks")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
