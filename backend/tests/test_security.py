
import pytest

from app.security import hash_password, verify_password


def test_hash_is_bcrypt_and_not_plaintext():
    password = "Strong123pw"

    hashed = hash_password(password)

    assert hashed.startswith(("$2a$", "$2b$", "$2y$"))
    assert hashed != password
    assert password not in hashed


def test_same_password_generates_different_salted_hashes():
    password = "Strong123pw"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash


def test_correct_password_is_verified():
    password = "Strong123pw"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_incorrect_password_is_rejected():
    hashed = hash_password("Strong123pw")

    assert verify_password("Wrong123pw", hashed) is False


def test_malformed_hash_does_not_crash():
    assert verify_password("Strong123pw", "not-a-bcrypt-hash") is False


def test_hash_rejects_password_over_72_utf8_bytes():
    # Each euro symbol occupies three UTF-8 bytes: 25 * 3 = 75.
    password = "€" * 25

    with pytest.raises(ValueError):
        hash_password(password)


def test_verify_rejects_password_over_72_utf8_bytes():
    hashed = hash_password("Strong123pw")

    assert verify_password("€" * 25, hashed) is False



def test_hash_rejects_non_string_password():
    with pytest.raises(TypeError):
        hash_password(None)


def test_verify_handles_bcrypt_verification_error(monkeypatch):
    import app.security as security

    def raise_invalid_hash(password_bytes, hashed_bytes):
        raise ValueError("Invalid hash format")

    monkeypatch.setattr(
        security.bcrypt,
        "checkpw",
        raise_invalid_hash,
    )

    assert verify_password("Strong123pw", "invalid-hash") is False

def test_verify_rejects_non_string_inputs():
    assert verify_password(None, "not-a-hash") is False
    assert verify_password("Strong123pw", None) is False
