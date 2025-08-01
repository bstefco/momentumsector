# Stock Analysis Serverless Handler

A serverless AWS Lambda function that provides comprehensive stock analysis including real-time Reddit mention data from Ape Wisdom.

## 🚀 Features

- **Real-time Stock Data**: Price, volume, market cap, and price changes
- **Short Interest Analysis**: Short interest percentage and shares short
- **Reddit Sentiment**: Real-time mentions from r/wallstreetbets via Ape Wisdom API
- **Slack Integration**: Beautiful Slack Block Kit formatted responses
- **Error Handling**: Comprehensive error handling and graceful degradation

## 📊 Data Sources

- **Yahoo Finance**: Stock price, volume, market cap, short interest
- **Ape Wisdom API**: Reddit mentions from r/wallstreetbets
- **Real-time Calculations**: Price changes, short interest percentages

## 🛠️ Architecture

- **Runtime**: Python 3.12
- **Platform**: AWS Lambda
- **API Gateway**: HTTP API Gateway integration
- **Dependencies**: requests, yfinance, pandas

## 📋 API Usage

### Request Format
```json
{
  "ticker": "TSLA"
}
```

### Response Format
Returns a Slack Block Kit formatted response with:
- Stock price and change percentage
- Market cap and volume
- Short interest data
- Reddit mentions (24h and change)
- Company information

### Example Response
```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🚀 TSLA Analysis",
        "emoji": true
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Price:* $250.00 (+4.17%)"
        },
        {
          "type": "mrkdwn",
          "text": "*Market Cap:* $50.0B"
        },
        {
          "type": "mrkdwn",
          "text": "*Volume:* 1.0M"
        },
        {
          "type": "mrkdwn",
          "text": "*Short Interest:* 5.0%"
        },
        {
          "type": "mrkdwn",
          "text": "*Reddit Mentions:* 🔥 150 (+50)"
        },
        {
          "type": "mrkdwn",
          "text": "*Sector:* Consumer Cyclical"
        }
      ]
    }
  ]
}
```

## 🔧 Ape Wisdom Integration

The handler includes the `apewisdom_mentions()` function that:

- Fetches data from Ape Wisdom API: `https://apewisdom.io/api/v1.0/filter/wallstreetbets`
- Returns `(mentions_24h, Δmentions_vs_24h_ago)` for the specified ticker
- Returns `(0, 0)` if the ticker isn't in the top-100 list
- Includes comprehensive error handling

### Function Signature
```python
def apewisdom_mentions(symbol: str) -> tuple[int, int]:
    """
    Return (mentions_24h, Δmentions_vs_24h_ago) for `symbol`.
    If the ticker isn't in the top-100 list, return (0, 0).
    """
```

## 🚀 Deployment

### Prerequisites
- AWS CLI configured
- Python 3.12
- Required dependencies installed

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_handler.py

# Test the handler locally
python handler.py
```

### AWS Lambda Deployment
1. Create a deployment package:
```bash
pip install -r requirements.txt -t package/
cp handler.py package/
cd package
zip -r ../lambda_function.zip .
```

2. Deploy to AWS Lambda:
```bash
aws lambda create-function \
  --function-name stock-analysis \
  --runtime python3.12 \
  --handler handler.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role
```

3. Configure API Gateway integration

## 🧪 Testing

Run the comprehensive test suite:
```bash
python -m pytest test_handler.py -v
```

### Test Coverage
- ✅ Ape Wisdom API integration
- ✅ Stock data retrieval
- ✅ Slack Block Kit formatting
- ✅ Error handling
- ✅ Lambda handler responses

## 📈 Performance

- **Cold Start**: ~2-3 seconds
- **Warm Start**: ~500ms
- **API Response Time**: ~1-2 seconds
- **Memory Usage**: 128MB (configurable)

## 🔒 Security

- Input validation for ticker symbols
- Error handling prevents information leakage
- CORS headers for web integration
- Rate limiting via API Gateway

## 🐛 Troubleshooting

### Common Issues

1. **Ape Wisdom API Errors**
   - Check API availability
   - Verify network connectivity
   - Review error logs

2. **Yahoo Finance Errors**
   - Verify ticker symbol validity
   - Check market hours
   - Review rate limiting

3. **Lambda Timeout**
   - Increase timeout setting
   - Optimize API calls
   - Add caching if needed

### Debug Mode
Enable detailed logging by setting the `LOG_LEVEL` environment variable:
```bash
export LOG_LEVEL=DEBUG
```

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the test cases for examples 