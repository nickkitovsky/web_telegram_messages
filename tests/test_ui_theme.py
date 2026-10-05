import pytest
from httpx import ASGITransport, AsyncClient

from saved_messages.main import app, home


@pytest.mark.asyncio
async def test_home_uses_nord_themes_and_local_reference_branding() -> None:
    html = (await home()).body.decode()

    assert 'href="/static/favicon.png"' in html
    assert 'src="/static/app-logo.png"' in html
    assert "--nord0:#2e3440" in html
    assert "--nord6:#eceff4" in html
    assert '#app-shell .side-item[aria-current="page"] svg' in html
    assert "#app-shell .menu-item:hover svg" in html
    assert "button:focus-visible" in html


@pytest.mark.asyncio
async def test_logo_and_favicon_are_served_as_local_png_assets() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        logo = await client.get("/static/app-logo.png")
        favicon = await client.get("/static/favicon.png")

    assert logo.status_code == 200
    assert favicon.status_code == 200
    assert logo.headers["content-type"] == "image/png"
    assert favicon.headers["content-type"] == "image/png"
    assert logo.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert favicon.content.startswith(b"\x89PNG\r\n\x1a\n")
