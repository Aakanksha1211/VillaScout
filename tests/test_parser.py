from villascout.services.enrichment.parser import WebsiteParser


def test_parser_extracts_amenities_contact_and_price() -> None:
    html = """
    <html>
      <body>
        <p>4 bedrooms, 5 bathrooms, sleeps 12 guests. Private pool, BBQ, WiFi.</p>
        <p>Check-in: 2 PM Check-out: 11 AM Price INR 25,000 per night</p>
        <a href="https://wa.me/919876543210">WhatsApp</a>
        <a href="https://instagram.com/casaverde">Instagram</a>
        <p>hello@example.com +91 9876543210</p>
        <img src="https://example.com/pool.jpg" />
      </body>
    </html>
    """
    amenities, contact, price, images = WebsiteParser().parse(html)

    assert amenities.bedrooms == 4
    assert amenities.bathrooms == 5
    assert amenities.guests == 12
    assert amenities.private_pool is True
    assert amenities.bbq is True
    assert amenities.wifi is True
    assert contact.email == "hello@example.com"
    assert contact.phone == "+91 9876543210"
    assert contact.whatsapp == "https://wa.me/919876543210"
    assert contact.instagram == "https://instagram.com/casaverde"
    assert price.amount == 25_000
    assert images == ["https://example.com/pool.jpg"]
