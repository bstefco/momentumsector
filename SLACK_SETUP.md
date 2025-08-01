# Slack App Setup Guide

## 🚀 **Complete Slack Integration Setup**

Follow these steps to connect your stock analysis Lambda function to Slack.

### **Step 1: Create Slack App**

1. **Go to Slack API Console**
   - Visit: https://api.slack.com/apps
   - Click "Create New App"
   - Choose "From scratch"

2. **Configure App Details**
   - **App Name**: `Stock Analysis Bot` (or your preferred name)
   - **Workspace**: Select your workspace
   - Click "Create App"

### **Step 2: Add Slash Command**

1. **Navigate to Slash Commands**
   - In the left sidebar, click "Slash Commands"
   - Click "Create New Command"

2. **Configure Command**
   - **Command**: `/analyze`
   - **Request URL**: `[YOUR_API_GATEWAY_URL]` (we'll get this after deployment)
   - **Short Description**: `Analyze stock with Reddit sentiment`
   - **Usage Hint**: `[TICKER]`
   - **Escape channels, users, and links**: ✅ Checked

3. **Save Command**
   - Click "Save"

### **Step 3: Configure OAuth & Permissions**

1. **Add Bot Token Scopes**
   - Go to "OAuth & Permissions" in the sidebar
   - Scroll to "Scopes" section
   - Add these Bot Token Scopes:
     - `chat:write` (to send messages)
     - `commands` (for slash commands)

2. **Install App to Workspace**
   - Scroll to "OAuth Tokens for Your Workspace"
   - Click "Install to Workspace"
   - Authorize the app

3. **Copy Bot Token**
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)
   - Save this for later use

### **Step 4: Deploy Lambda Function**

1. **Install AWS SAM CLI** (if not already installed)
   ```bash
   # macOS
   brew install aws-sam-cli
   
   # Windows
   # Download from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install-windows.html
   
   # Linux
   pip install aws-sam-cli
   ```

2. **Configure AWS CLI**
   ```bash
   aws configure
   # Enter your AWS Access Key ID
   # Enter your AWS Secret Access Key
   # Enter your default region (e.g., us-east-1)
   ```

3. **Deploy the Function**
   ```bash
   # Build the application
   sam build
   
   # Deploy (first time)
   sam deploy --guided
   
   # Follow the prompts:
   # - Stack Name: stock-analysis-bot
   # - AWS Region: us-east-1 (or your preferred region)
   # - Confirm changes: Y
   # - Allow SAM CLI IAM role creation: Y
   # - Save arguments to configuration file: Y
   ```

4. **Get the API URL**
   - After deployment, SAM will output the API Gateway URL
   - Copy the URL that looks like: `https://abc123.execute-api.us-east-1.amazonaws.com/prod/analyze`

### **Step 5: Connect Slack to Lambda**

1. **Update Slack App Request URL**
   - Go back to your Slack app settings
   - Navigate to "Slash Commands"
   - Click "Edit" on your `/analyze` command
   - Update the "Request URL" with your API Gateway URL
   - Click "Save"

2. **Test the Integration**
   - Go to any channel in your Slack workspace
   - Type: `/analyze TSLA`
   - You should see a beautiful card with stock data and Reddit mentions!

### **Step 6: Optional - Add App to Channels**

1. **Invite Bot to Channels**
   - In any channel where you want to use the command
   - Type: `/invite @Stock Analysis Bot`

2. **Set Up Permissions**
   - The bot will automatically have permission to post in channels where it's invited

## 🧪 **Testing Your Setup**

### **Test Commands**
```
/analyze TSLA
/analyze AAPL
/analyze GME
/analyze NVDA
```

### **Expected Response**
You should see a Slack card with:
- 🚀 Stock price and change percentage
- 📊 Market cap and volume
- 📈 Short interest data
- 🔥 Reddit mentions from Ape Wisdom
- 🏢 Company information

## 🔧 **Troubleshooting**

### **Common Issues**

1. **"Command not found"**
   - Make sure the app is installed to your workspace
   - Check that the slash command is properly configured

2. **"Request failed"**
   - Verify the API Gateway URL is correct
   - Check CloudWatch logs for Lambda errors
   - Ensure the Lambda function deployed successfully

3. **"No response"**
   - Check that the bot has `chat:write` permission
   - Verify the Lambda function is returning the correct format

### **Debug Steps**

1. **Check Lambda Logs**
   ```bash
   # Get function name
   aws cloudformation describe-stacks --stack-name stock-analysis-bot --query 'Stacks[0].Outputs[?OutputKey==`FunctionName`].OutputValue' --output text
   
   # View logs
   aws logs tail /aws/lambda/[FUNCTION_NAME] --follow
   ```

2. **Test Lambda Directly**
   ```bash
   # Test the function
   aws lambda invoke --function-name [FUNCTION_NAME] --payload '{"body":"{\"ticker\":\"TSLA\"}"}' response.json
   cat response.json
   ```

3. **Check API Gateway**
   ```bash
   # Test the API endpoint
   curl -X POST [YOUR_API_URL] \
     -H "Content-Type: application/json" \
     -d '{"ticker":"TSLA"}'
   ```

## 🎉 **Success!**

Once everything is working, you'll have:
- ✅ Real-time stock analysis via Slack
- ✅ Reddit sentiment data from Ape Wisdom
- ✅ Beautiful Slack Block Kit responses
- ✅ Serverless architecture that scales automatically

## 📞 **Need Help?**

If you encounter issues:
1. Check the troubleshooting section above
2. Review CloudWatch logs for detailed error messages
3. Verify all AWS permissions are correct
4. Ensure the Slack app is properly configured

## 🔄 **Updates**

To update the function later:
```bash
sam build
sam deploy
```

The Slack integration will continue working without any changes needed! 