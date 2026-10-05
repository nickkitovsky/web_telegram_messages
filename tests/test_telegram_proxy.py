import pytest
from python_socks import ProxyType

from saved_messages.telegram import parse_proxy_url


@pytest.mark.parametrize(
    ("url", "proxy_type"),
    [
        ("socks5://localhost:1080", ProxyType.SOCKS5),
        ("socks4://localhost:1081", ProxyType.SOCKS4),
        ("http://localhost:8080", ProxyType.HTTP),
    ],
)
def test_parse_proxy_url(url: str, proxy_type: ProxyType) -> None:
    proxy = parse_proxy_url(url)

    assert proxy["proxy_type"] == proxy_type
    assert proxy["addr"] == "localhost"
    assert proxy["rdns"] is True


def test_parse_proxy_url_decodes_credentials() -> None:
    proxy = parse_proxy_url("socks5://user%40name:p%3Ass@localhost:1080")

    assert proxy["username"] == "user@name"
    assert proxy["password"] == "p:ss"


@pytest.mark.parametrize(
    "url",
    [
        "localhost:1080",
        "ftp://localhost:21",
        "socks5://localhost",
    ],
)
def test_parse_proxy_url_rejects_invalid_urls(url: str) -> None:
    with pytest.raises(ValueError, match="TELEGRAM_PROXY_URL"):
        parse_proxy_url(url)
