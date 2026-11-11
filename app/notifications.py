import httpx

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


async def notify_admin_about_lead(lead: dict) -> bool:
    """Send a Telegram message when credentials are configured.

    Returns False when Telegram is not configured. HTTP delivery failures
    are intentionally non-fatal: a lead must still be saved in the database.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    message = (
        "Новая заявка #{id}\n"
        "Имя: {name}\n"
        "Телефон: {phone}\n"
        "Услуга: {service}\n"
        "Описание: {message}"
    ).format(**lead)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            )
            response.raise_for_status()
        return True
    except httpx.HTTPError:
        # Do not lose a saved lead because Telegram is temporarily unavailable.
        return False
