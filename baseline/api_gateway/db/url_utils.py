"""Shared helpers for database connection URLs."""

from __future__ import annotations

from urllib.parse import quote, unquote


def normalize_db_url(url: str) -> str:
    """
    URL-encode the password segment of a ``postgresql://`` (or similar) DSN.

    Uses the *last* ``@`` as the boundary between userinfo and host so passwords
    may contain ``@``, ``/``, or ``?``. Splits user from password on the *first*
    ``:`` in the userinfo.
    """
    if "://" not in url or "@" not in url:
        return url

    scheme, rest = url.split("://", 1)
    userinfo, host_and_path = rest.rsplit("@", 1)
    if ":" not in userinfo:
        return url

    user, password = userinfo.split(":", 1)
    encoded_password = quote(unquote(password), safe="")
    return f"{scheme}://{user}:{encoded_password}@{host_and_path}"
