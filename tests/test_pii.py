from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out

def test_scrub_phone() -> None:
    out = scrub_text("Call me at +84 123 456 789")
    assert "123" not in out
    assert "REDACTED_PHONE" in out

def test_scub_cc() -> None:
    out = scrub_text("My credit card is 4111 1111 1111 1111")
    assert "4111" not in out
    assert "REDACTED_CC" in out
