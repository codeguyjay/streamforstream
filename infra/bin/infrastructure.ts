#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { BackendStack } from "../lib/backend-stack";
import { DdbStorageStack } from "../lib/ddb-storage-stack";
import { DEFAULT_ACCOUNT, PRIMARY_REGION } from "../lib/config";
import { FrontendStack } from "../lib/frontend-stack";

const app = new cdk.App();
const account = process.env.CDK_DEFAULT_ACCOUNT ?? DEFAULT_ACCOUNT;
const env = { account, region: PRIMARY_REGION };

cdk.Tags.of(app).add("Project", "StreamBaton");

const ddbStack = new DdbStorageStack(app, "DdbStorageStack", {
  env,
});

const backendStack = new BackendStack(app, "BackendStack", {
  env,
  ddbStack,
});

const frontendStack = new FrontendStack(app, "FrontendStack", {
  env,
});
frontendStack.addDependency(backendStack);
