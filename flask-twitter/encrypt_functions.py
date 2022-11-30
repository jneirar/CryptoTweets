from tinyec import registry, ec
from Crypto.Cipher import AES
import hashlib, secrets, binascii

curve = registry.get_curve('brainpoolP256r1')

def private_key_to_string(private_key):
    return hex(private_key)

def string_to_private_key(private_key_string):
    return int(private_key_string, 16)

def public_key_to_string(public_key_string):
    x = str(hex(public_key_string.x))[2:].zfill(64)
    y = str(hex(public_key_string.y))[2:].zfill(64)
    return x + y

def string_to_public_key(public_key_string):
    x = int(public_key_string[:64], 16)
    y = int(public_key_string[64:], 16)
    return ec.Point(curve, x, y)

def generate_keys():
    private_key = secrets.randbelow(curve.field.n)
    public_key = private_key * curve.g
    return (private_key, public_key)

def encrypt_AES_GCM(msg, secretKey):
    aesCipher = AES.new(secretKey, AES.MODE_GCM)
    ciphertext, authTag = aesCipher.encrypt_and_digest(msg)
    return (ciphertext, aesCipher.nonce, authTag)

def decrypt_AES_GCM(ciphertext, nonce, authTag, secretKey):
    aesCipher = AES.new(secretKey, AES.MODE_GCM, nonce)
    plaintext = aesCipher.decrypt_and_verify(ciphertext, authTag)
    return plaintext

def ecc_point_to_256_bit_key(point):
    sha = hashlib.sha256(int.to_bytes(point.x, 32, 'big'))
    sha.update(int.to_bytes(point.y, 32, 'big'))
    return sha.digest()

def encrypt_ECC(msg, pubKeyReceiver, privKeySender):
    sharedECCKey = privKeySender * pubKeyReceiver
    secretKey = ecc_point_to_256_bit_key(sharedECCKey)
    ciphertext, nonce, authTag = encrypt_AES_GCM(msg, secretKey)
    return (ciphertext, nonce, authTag)

def decrypt_ECC(encryptedMsg, privKeyReceiver, pubKeySender):
    (ciphertext, nonce, authTag) = encryptedMsg
    sharedECCKey = privKeyReceiver * pubKeySender
    secretKey = ecc_point_to_256_bit_key(sharedECCKey)
    plaintext = decrypt_AES_GCM(ciphertext, nonce, authTag, secretKey)
    return plaintext

def decrypt_ECC_sender(encryptedMsg, privKeySender, pubKeyReceiver):
    (ciphertext, nonce, authTag) = encryptedMsg
    sharedECCKey = privKeySender * pubKeyReceiver
    secretKey = ecc_point_to_256_bit_key(sharedECCKey)
    plaintext = decrypt_AES_GCM(ciphertext, nonce, authTag, secretKey)
    return plaintext
