import * as cdk from "aws-cdk-lib";
import * as acm from "aws-cdk-lib/aws-certificatemanager";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as ecsPatterns from "aws-cdk-lib/aws-ecs-patterns";
import * as route53 from "aws-cdk-lib/aws-route53";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as path from "node:path";
import { Construct } from "constructs";
import type { DdbStorageStack } from "./ddb-storage-stack";
import {
  API_DOMAIN_NAME,
  DOMAIN_NAME,
  FRONTEND_ORIGINS,
  STREAMER_STATE_TABLE_NAME,
  TWITCH_SECRET_NAME,
  VIEW_REPORTS_TABLE_NAME,
} from "./config";

export interface BackendStackProps extends cdk.StackProps {
  ddbStack: DdbStorageStack;
}

export class BackendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BackendStackProps) {
    super(scope, id, props);

    const streamerStateTable = dynamodb.Table.fromTableName(
      this,
      "ImportedStreamerStateTable",
      STREAMER_STATE_TABLE_NAME,
    );
    const viewReportsTable = dynamodb.Table.fromTableName(
      this,
      "ImportedViewReportsTable",
      VIEW_REPORTS_TABLE_NAME,
    );

    const vpc = new ec2.Vpc(this, "Vpc", { maxAzs: 2 });
    const cluster = new ecs.Cluster(this, "Cluster", { vpc });
    const twitchSecret = secretsmanager.Secret.fromSecretNameV2(
      this,
      "TwitchSecret",
      TWITCH_SECRET_NAME
    );

    const zone = route53.HostedZone.fromLookup(this, "Zone", {
      domainName: DOMAIN_NAME,
    });
    const certificate = new acm.Certificate(this, "ApiCertificate", {
      domainName: API_DOMAIN_NAME,
      validation: acm.CertificateValidation.fromDns(zone),
    });

    const fargateService = new ecsPatterns.ApplicationLoadBalancedFargateService(
      this,
      "StreamBatonBackendFargateService",
      {
        cluster,
        cpu: 256,
        memoryLimitMiB: 512,
        desiredCount: 1,
        publicLoadBalancer: true,
        redirectHTTP: true,
        certificate,
        domainName: API_DOMAIN_NAME,
        domainZone: zone,
        taskImageOptions: {
          image: ecs.ContainerImage.fromAsset(
            path.join(__dirname, "..", "..", "backend")
          ),
          containerPort: 8080,
          environment: {
            AWS_REGION: this.region,
            FRONTEND_ORIGIN: FRONTEND_ORIGINS[0],
            FRONTEND_ORIGINS: FRONTEND_ORIGINS.join(","),
            STREAMING_STORE_BACKEND: "dynamodb",
            DDB_STREAMER_STATE_TABLE_NAME: STREAMER_STATE_TABLE_NAME,
            DDB_VIEW_REPORTS_TABLE_NAME: VIEW_REPORTS_TABLE_NAME,
            TWITCH_SWEEPER_INTERVAL_SECONDS:
              (this.node.tryGetContext(
                "twitchSweeperIntervalSeconds"
              ) as string | undefined) ?? "300",
          },
          secrets: {
            TWITCH_CLIENT_ID: ecs.Secret.fromSecretsManager(
              twitchSecret,
              "TWITCH_CLIENT_ID"
            ),
            TWITCH_CLIENT_SECRET: ecs.Secret.fromSecretsManager(
              twitchSecret,
              "TWITCH_CLIENT_SECRET"
            ),
          },
        },
      }
    );

    fargateService.targetGroup.configureHealthCheck({
      path: "/health",
      healthyHttpCodes: "200",
    });

    twitchSecret.grantRead(fargateService.taskDefinition.executionRole!);

    const taskRole = fargateService.taskDefinition.taskRole;
    if (taskRole) {
      streamerStateTable.grantReadWriteData(taskRole);
      viewReportsTable.grantReadWriteData(taskRole);
    }

    new cdk.CfnOutput(this, "BackendURL", {
      value: `https://${API_DOMAIN_NAME}`,
      description: "Backend API base URL",
      exportName: "StreamBatonBackendURL",
    });
    new cdk.CfnOutput(this, "BackendAlbDnsName", {
      value: fargateService.loadBalancer.loadBalancerDnsName,
      description: "Application Load Balancer DNS name",
      exportName: "StreamBatonBackendAlbDnsName",
    });
  }
}
