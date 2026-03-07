import * as amplify from "@aws-cdk/aws-amplify-alpha";
import * as cdk from "aws-cdk-lib";
import * as codebuild from "aws-cdk-lib/aws-codebuild";
import * as iam from "aws-cdk-lib/aws-iam";
import * as route53 from "aws-cdk-lib/aws-route53";
import { Construct } from "constructs";
import {
  DOMAIN_NAME,
  FRONTEND_APP_NAME,
  FRONTEND_APP_ROOT,
  GITHUB_BRANCH,
  GITHUB_OWNER,
  GITHUB_REPO,
  GITHUB_TOKEN_SECRET_NAME,
} from "./config";

export interface FrontendStackProps extends cdk.StackProps {
  environmentVariables?: Record<string, string>;
}

export class FrontendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: FrontendStackProps) {
    super(scope, id, props);

    const backendUrl = cdk.Fn.importValue("StreamBatonBackendURL");
    const token = cdk.SecretValue.secretsManager(GITHUB_TOKEN_SECRET_NAME);

    const buildSpecObject: Record<string, unknown> = {
      version: 1,
      applications: [
        {
          appRoot: FRONTEND_APP_ROOT,
          frontend: {
            phases: {
              preBuild: { commands: ["npm ci"] },
              build: { commands: ["npm run build"] },
            },
            artifacts: {
              baseDirectory: ".next",
              files: ["**/*"],
            },
            cache: {
              paths: ["node_modules/**/*"],
            },
          },
        },
      ],
    };

    const amplifyApp = new amplify.App(this, "App", {
      appName: FRONTEND_APP_NAME,
      sourceCodeProvider: new amplify.GitHubSourceCodeProvider({
        owner: GITHUB_OWNER,
        repository: GITHUB_REPO,
        oauthToken: token,
      }),
      platform: amplify.Platform.WEB_COMPUTE,
      buildSpec: codebuild.BuildSpec.fromObjectToYaml(buildSpecObject),
      environmentVariables: {
        ...(props?.environmentVariables ?? {}),
        NEXT_PUBLIC_API_BASE_URL: backendUrl,
        AMPLIFY_MONOREPO_APP_ROOT: FRONTEND_APP_ROOT,
      },
    });

    const mainBranch = amplifyApp.addBranch("main", {
      branchName: GITHUB_BRANCH,
      autoBuild: true,
      pullRequestPreview: true,
    });

    const zone = route53.HostedZone.fromLookup(this, "Zone", {
      domainName: DOMAIN_NAME,
    });

    const amplifyDomainRole = new iam.Role(this, "AmplifyDomainRole", {
      roleName: `AWSAmplifyDomainRole-${zone.hostedZoneId}`,
      assumedBy: new iam.ServicePrincipal("amplify.amazonaws.com"),
      inlinePolicies: {
        AmplifyDomainManagement: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              actions: [
                "route53:ChangeResourceRecordSets",
                "route53:ListResourceRecordSets",
                "route53:GetHostedZone",
              ],
              resources: [zone.hostedZoneArn],
            }),
            new iam.PolicyStatement({
              actions: ["route53:ListHostedZones"],
              resources: ["*"],
            }),
          ],
        }),
      },
    });

    const domain = amplifyApp.addDomain("Domain", {
      domainName: DOMAIN_NAME,
    });
    domain.mapRoot(mainBranch);
    domain.mapSubDomain(mainBranch, "www");
    domain.node.addDependency(amplifyDomainRole);

    new cdk.CfnOutput(this, "WebsiteURL", {
      value: `https://${DOMAIN_NAME}`,
      description: "Frontend URL",
      exportName: "StreamBatonFrontendURL",
    });
    new cdk.CfnOutput(this, "AmplifyAppId", {
      value: amplifyApp.appId,
      description: "Amplify App ID",
      exportName: "StreamBatonAmplifyAppId",
    });
  }
}
