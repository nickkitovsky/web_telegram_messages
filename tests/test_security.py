from saved_messages.security import hash_password, token_digest, verify_password


def test_password_hash_verifies_without_storing_plaintext() -> None:
    password = "correct horse battery staple"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("incorrect", hashed)


def test_session_token_digest_is_stable() -> None:
    assert token_digest("opaque-token") == token_digest("opaque-token")
    assert token_digest("opaque-token") != token_digest("different-token")
