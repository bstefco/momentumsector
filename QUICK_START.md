# 🚀 Quick Start Guide - Stock Analysis Slack Bot

## **Complete Setup in 5 Minutes**

### **Prerequisites**
- AWS account with CLI access
- Slack workspace where you have admin permissions

### **Step 1: Install Tools**
```bash
# Install AWS SAM CLI
brew install aws-sam-cli  # macOS
# or download from AWS website for Windows/Linux

# Configure AWS CLI
aws configure
# Enter your AWS credentials and region
```

### **Step 2: Deploy to AWS**
```bash
# Run the deployment script
./deploy.sh

# Follow the prompts:
# - Stack Name: stock-analysis-bot
# - Region: us-east-1 (or your preferred region)
# - Confirm: Y
# - Allow IAM role creation: Y
```

### **Step 3: Create Slack App**
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: `Stock Analysis Bot`
4. Select your workspace

### **Step 4: Configure Slack Command**
1. In your app, go to "Slash Commands"
2. Click "Create New Command"
3. Configure:
   - **Command**: `/analyze`
   - **Request URL**: `[API_URL_FROM_DEPLOYMENT]`
   - **Description**: `Analyze stock with Reddit sentiment`
4. Save

### **Step 5: Install App**
1. Go to "OAuth & Permissions"
2. Add scopes: `chat:write`, `commands`
3. Click "Install to Workspace"
4. Authorize

### **Step 6: Test**
In any Slack channel, type:
```
/analyze TSLA
```

You should see a beautiful card with stock data and Reddit mentions! 🎉

## **What You Get**

✅ **Real-time stock analysis** via Slack slash command  
✅ **Reddit sentiment data** from Ape Wisdom  
✅ **Beautiful Slack cards** with emojis and formatting  
✅ **Serverless architecture** that scales automatically  
✅ **No maintenance required** - runs on AWS Lambda  

## **Usage Examples**

```
/analyze TSLA    # Tesla with Reddit mentions
/analyze AAPL    # Apple stock analysis
/analyze GME     # GameStop with sentiment
/analyze NVDA    # NVIDIA analysis
```

## **Need Help?**

- 📖 **Detailed Setup**: See `SLACK_SETUP.md`
- 🐛 **Troubleshooting**: Check CloudWatch logs
- 🔧 **Updates**: Run `sam build && sam deploy`

## **Costs**

- **AWS Lambda**: ~$0.20 per 1M requests
- **API Gateway**: ~$3.50 per 1M requests
- **Slack**: Free for basic usage

**Total**: Less than $5/month for normal usage! 