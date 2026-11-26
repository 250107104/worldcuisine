from app.security import hash_password, verify_password


def test_passwords_are_stored_as_argon2id_hashes():
    password = "correct horse battery staple"
    encoded = hash_password(password)

    assert encoded != password
    assert encoded.startswith("$argon2id$")
    assert verify_password(password, encoded)
    assert not verify_password("not the password", encoded)
