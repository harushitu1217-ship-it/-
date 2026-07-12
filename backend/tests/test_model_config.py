from app.modules.providers.crypto import SecretCipher


def test_secret_cipher_does_not_store_plaintext():
    cipher = SecretCipher("test-secret")

    encrypted = cipher.encrypt("sk-private")

    assert "sk-private" not in encrypted
    assert cipher.decrypt(encrypted) == "sk-private"
