from app.core.security import hash_password, verify_password


def test_password_hash_and_verification_round_trip():
    password = "StrongPassword!123"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("WrongPassword!123", password_hash) is False


def test_verify_password_rejects_invalid_hashes():
    assert verify_password("password", "not-a-valid-argon2-hash") is False
    assert verify_password("password", "") is False
