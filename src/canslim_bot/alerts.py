import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SlackAlerter:
    """
    SlackAlerter sends formatted messages to a Slack channel via webhook.
    """
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, message: str) -> None:
        """
        Send a plain text message to Slack.
        """
        if self.webhook_url:
            resp = requests.post(self.webhook_url, json={"text": message})
            if resp.status_code != 200:
                logger.error(f"Slack webhook failed: {resp.text}")

    def send_startup(self) -> None:
        """
        Send a startup notification to Slack.
        """
        self.send(":robot_face: CANSLIM Slack Bot started.")

    def send_buy(self, payload: Dict[str, Any]) -> None:
        """
        Send a formatted BUY alert to Slack.
        Payload keys: tkr, entry, pivot, stop, target, vol_ratio, rs1, rs6, size_pct
        """
        msg = (
            f"*BUY* {payload['tkr']}\n"
            f"Entry: {payload['entry']:.2f}, Pivot: {payload['pivot']:.2f}, Stop: {payload['stop']:.2f}, Target: {payload['target']:.2f}\n"
            f"Vol Ratio: {payload['vol_ratio']:.2f}, RS(1w): {payload['rs1']:.1f}, RS(6m): {payload['rs6']:.1f}, Size: {payload['size_pct']:.2f}%"
        )
        self.send(msg)

    def send_sell(self, payload: Dict[str, Any]) -> None:
        """
        Send a formatted SELL alert to Slack.
        Payload keys: tkr, reason, exit_price, entry, gain_pct
        """
        msg = (
            f"*SELL* {payload['tkr']}\n"
            f"Reason: {payload['reason']}\n"
            f"Exit: {payload['exit_price']:.2f}, Entry: {payload['entry']:.2f}, Gain: {payload['gain_pct']:.2f}%"
        )
        self.send(msg) 