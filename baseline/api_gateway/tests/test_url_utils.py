from urllib.parse import unquote

from db.url_utils import normalize_db_url


def test_normalize_password_with_at_slash_question():
    raw = "postgresql://postgres:ZF6d!J@U6S/?U?v@db.example.com:5432/postgres"
    out = normalize_db_url(raw)
    assert out.startswith("postgresql://postgres:")
    assert "@db.example.com:5432/postgres" in out
    # password segment is percent-encoded
    _, rest = out.split("://", 1)
    userinfo, host = rest.rsplit("@", 1)
    user, pw_encoded = userinfo.split(":", 1)
    assert user == "postgres"
    assert unquote(pw_encoded) == "ZF6d!J@U6S/?U?v"
    assert host == "db.example.com:5432/postgres"
