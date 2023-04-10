from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_dynamodb as dynamodb,
    aws_xray as xray,
    RemovalPolicy,
    Duration
)
from constructs import Construct

class RaghavStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # Create an IAM Role for the EC2 instance
        ec2_role = iam.Role(
            self,
            "EC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        # Attach an IAM policy to the role that allows the EC2 instance to make HTTP requests
        ec2_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces"],
                resources=["*"],
            )
        )


        # create a new IAM role for the Lambda function
        db_role = iam.Role(
            self, 'DBIAMRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            role_name='DBLambdaRole',
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
            ]
        )
        db_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents',
                    'states:StartExecution',
                    "events:PutEvents",
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets",
                    "dynamodb:PutItem"
                ],
                resources=['*']
            )
        )

        route_role = iam.Role(
            self, 'RouteLambdaIAMRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            role_name='RouteLambdaRole',
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
            ]
        )
        route_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents',
                    "events:PutEvents",
                    "route53:CreateHostedZone",
                    "route53:ChangeResourceRecordSets",
                    "acm:RequestCertificate",
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets",
                    "execute-api:Invoke"
                ],
                resources=['*']
            )
        )        

        execute_sf_lambda= lambda_.Function(self, "startstepfunctionlambda",
                                                       function_name="start_stepfunction_lambda",
                                                       handler="lambda_function.lambda_handler",
                                                       runtime=lambda_.Runtime.PYTHON_3_9,
                                                       code=lambda_.Code.from_asset(
                                                           "lambda_code/execute_lambda"),
                                                       timeout=Duration.seconds(10),
                                                       environment={
                                                            "StateMachine":"Ec2_A_Record"
                                                       },
                                                       role=db_role,
                                                       tracing=lambda_.Tracing.ACTIVE)
        dynamodb_lambda=lambda_.Function(
                            self,
                            "DynamodbLambda",
                            runtime=lambda_.Runtime.PYTHON_3_8,
                            function_name='Dynamodb_lambda',
                            handler="lambda_function.lambda_handler",
                            code=lambda_.Code.from_asset("lambda_code/dynamodb_lambda"),
                            role=db_role,
                            environment={"table_name":"Arecord_table_name"},
                            timeout=Duration.seconds(10),
                            tracing=lambda_.Tracing.ACTIVE,
                        )                                               
        route53_lambda= lambda_.Function(
                                    self,
                                    "Route53Lambda",
                                    function_name='Route53_lambda',
                                    runtime=lambda_.Runtime.PYTHON_3_8,
                                    handler="lambda_function.lambda_handler",
                                    code=lambda_.Code.from_asset("lambda_code/route53_lambda"),
                                    role=route_role,
                                    timeout=Duration.seconds(10),
                                    tracing=lambda_.Tracing.ACTIVE,
                                )

        # Define the first Lambda function state
        dynamodb_sf_task = tasks.LambdaInvoke(
            self,
            "DynamodbStepFunctionTask",
            lambda_function=dynamodb_lambda
        )
        # Define the second Lambda function state
        route53_sf_task = tasks.LambdaInvoke(
            self,
            "Route53StepFunctionTask",
            lambda_function=route53_lambda
        )

        parallel_state = sfn.Parallel(
            self, 'ParallelState'
        )

        # add the tasks to the parallel state
        parallel_state.branch(dynamodb_sf_task)
        parallel_state.branch(route53_sf_task)
        # Define the Step Functions state machine
        step_fn = sfn.StateMachine(
            self,
            "StepFn",
            timeout=Duration.minutes(5),
            tracing_enabled=True,
            state_machine_name="Ec2_A_Record",
            state_machine_type=sfn.StateMachineType.STANDARD,
            definition=parallel_state
            )

       
        api = apigw.RestApi(
            self,
            "EC2API",
            rest_api_name="EC2API"
        )

        execute_resource = api.root.add_resource("A_Record")
        execute_method = execute_resource.add_method(
            "POST",
            apigw.LambdaIntegration(execute_sf_lambda),
            request_models={'application/json': apigw.Model.EMPTY_MODEL}
        )



        account_db = dynamodb.Table(
            self, 'AccountDB',
            partition_key=dynamodb.Attribute(
                name='domain_name',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            table_name='Arecord_table_name',
            removal_policy=RemovalPolicy.DESTROY,
        )        