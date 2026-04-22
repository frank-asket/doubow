async def create_draft(user_id: str, to: str, subject: str, body: str) -> str:
    """Gmail API **draft creation** is not wired yet — outbound send uses Gmail API elsewhere.

    Marketing copy (“drafts you edit and send from your own address”) reflects the intended UX:
    connect Google OAuth, approve an email-channel draft in Approvals, then **send via Gmail API**
    from the connected Google account (see `send_gmail_message`). Saving a native Gmail **draft** for
    later editing
    would require additional Gmail scopes and implementation here.
    """
    return 'draft-id'
