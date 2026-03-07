import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import { Construct } from "constructs";
import {
  STREAMER_STATE_TABLE_NAME,
  VIEW_REPORTS_TABLE_NAME,
} from "./config";

/**
 * DynamoDB tables for the StreamBaton backend.
 * Table keys and index names match backend/app/storage/dynamodb.py.
 */
export class DdbStorageStack extends cdk.Stack {
  public readonly streamerStateTable: dynamodb.Table;
  public readonly viewReportsTable: dynamodb.Table;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.streamerStateTable = new dynamodb.Table(this, "StreamerStateTable", {
      tableName: STREAMER_STATE_TABLE_NAME,
      partitionKey: {
        name: "channel_login",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
    this.streamerStateTable.addGlobalSecondaryIndex({
      indexName: "live_viewers",
      partitionKey: {
        name: "live_viewers_pk",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "live_viewers_sk",
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });
    this.streamerStateTable.addGlobalSecondaryIndex({
      indexName: "live_engagement",
      partitionKey: {
        name: "live_engagement_pk",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "live_engagement_sk",
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    this.viewReportsTable = new dynamodb.Table(this, "ViewReportsTable", {
      tableName: VIEW_REPORTS_TABLE_NAME,
      partitionKey: {
        name: "viewer_channel_login",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "viewed_minute",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    new cdk.CfnOutput(this, "StreamerStateTableName", {
      value: this.streamerStateTable.tableName,
      description: "Primary streamer state table",
      exportName: "StreamBatonStreamerStateTableName",
    });
    new cdk.CfnOutput(this, "ViewReportsTableName", {
      value: this.viewReportsTable.tableName,
      description: "Deduplicated viewing minute reports table",
      exportName: "StreamBatonViewReportsTableName",
    });
  }
}
