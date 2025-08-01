#!/bin/bash

# Stock Analysis Bot Deployment Script
# This script deploys the Lambda function to AWS

set -e  # Exit on any error

echo "🚀 Starting Stock Analysis Bot Deployment..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first:"
    echo "   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if AWS SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI is not installed. Please install it first:"
    echo "   https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Build the application
echo "🔨 Building application..."
sam build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build completed"

# Deploy the application
echo "🚀 Deploying to AWS..."
echo "   This will create the Lambda function and API Gateway"
echo "   Follow the prompts below:"

sam deploy --guided

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed"
    exit 1
fi

echo "✅ Deployment completed!"

# Get the API URL
echo "📋 Getting API Gateway URL..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name stock-analysis-bot \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text 2>/dev/null || echo "Could not retrieve API URL")

if [ "$API_URL" != "Could not retrieve API URL" ]; then
    echo ""
    echo "🎉 DEPLOYMENT SUCCESSFUL!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Go to https://api.slack.com/apps"
    echo "2. Create a new Slack app"
    echo "3. Add a slash command '/analyze'"
    echo "4. Set the Request URL to: $API_URL"
    echo "5. Install the app to your workspace"
    echo ""
    echo "📖 See SLACK_SETUP.md for detailed instructions"
    echo ""
    echo "🧪 Test the API:"
    echo "curl -X POST $API_URL \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"ticker\":\"TSLA\"}'"
else
    echo ""
    echo "⚠️  Deployment completed but couldn't retrieve API URL"
    echo "   Check the AWS CloudFormation console for the stack outputs"
fi

echo ""
echo "🔧 Useful Commands:"
echo "   View logs: sam logs -n StockAnalysisFunction --tail"
echo "   Update function: sam build && sam deploy"
echo "   Delete stack: sam delete" 