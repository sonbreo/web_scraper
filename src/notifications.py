import logging
import smtplib
import os
from email.message import EmailMessage
from typing import Optional

import requests

from .parser import Listing

logger = logging.getLogger(__name__)


def notify(listings: list[Listing], config: dict) -> None:
    if not listings:
        return
    notif_cfg = config.get("features", {}).get("notifications", {})
    if notif_cfg.get("email", False):
        _send_email(listings, notif_cfg.get("email_config", {}))
    if notif_cfg.get("discord", False):
        _send_discord(listings, notif_cfg.get("discord_webhook"))


def _send_email(listings: list[Listing], cfg: dict) -> None:
    smtp_host = cfg.get("smtp_host") or os.getenv("SMTP_HOST", "")
    smtp_port = int(cfg.get("smtp_port") or os.getenv("SMTP_PORT", 587))
    username = cfg.get("username") or os.getenv("SMTP_USERNAME", "")
    password = cfg.get("password") or os.getenv("SMTP_PASSWORD", "")
    sender = cfg.get("from") or os.getenv("SMTP_FROM", username)
    recipient = cfg.get("to") or os.getenv("SMTP_TO", "")

    if not all([smtp_host, username, password, recipient]):
        logger.warning("Email notification skipped: incomplete SMTP config")
        return

    msg = EmailMessage()
    msg["Subject"] = f"Gumtree: {len(listings)} new listing(s) found"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(_format_email_body(listings))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        logger.info("Email sent to %s with %d listing(s)", recipient, len(listings))
    except Exception as exc:
        logger.error("Failed to send email: %s", exc)


def _send_discord(listings: list[Listing], webhook_url: Optional[str]) -> None:
    webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "")
    if not webhook_url:
        logger.warning("Discord notification skipped: no webhook URL configured")
        return

    for listing in listings:
        payload = {
            "embeds": [{
                "title": listing.title,
                "url": listing.url,
                "description": (
                    f"**Price:** {listing.price_raw}\n"
                    f"**Location:** {listing.location or 'N/A'}\n"
                    f"**Posted:** {listing.date_raw or 'N/A'}\n"
                    f"**Seller:** {listing.seller_type}"
                ),
                "color": 0x00B0F4,
                **({"thumbnail": {"url": listing.thumbnail_url}} if listing.thumbnail_url else {}),
            }]
        }
        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.debug("Discord notification sent for listing %s", listing.listing_id)
        except Exception as exc:
            logger.error("Failed to send Discord notification for %s: %s", listing.listing_id, exc)


def _format_email_body(listings: list[Listing]) -> str:
    lines = [f"Found {len(listings)} new Gumtree listing(s):\n"]
    for l in listings:
        lines.append(f"- {l.title}")
        lines.append(f"  Price: {l.price_raw}")
        lines.append(f"  Location: {l.location or 'N/A'}")
        lines.append(f"  Posted: {l.date_raw or 'N/A'}")
        lines.append(f"  {l.url}\n")
    return "\n".join(lines)
