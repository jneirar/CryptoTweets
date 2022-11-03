from encrypt_functions import *

msg = b'Hola Bob, como estas?'
print("original msg:", msg)
privKeyAlice, pubKeyAlice = generate_keys()
privKeyBob, pubKeyBob = generate_keys()
first = pubKeyAlice.x
second = pubKeyAlice.y
limit = 64
# first to hex string with limit characters, fill with spaces
first = str(hex(first))[2:].zfill(limit)
second = str(hex(second))[2:].zfill(limit)
# Generate tinyec point with first and second
pub = ec.Point(curve, int(first,16), int(second,16))
#remove 0 leading and convert to int

encryptedMsg = encrypt_ECC(msg, pubKeyBob, privKeyAlice)
encryptedMsgObj = {
    'ciphertext': binascii.hexlify(encryptedMsg[0]),
    'nonce': binascii.hexlify(encryptedMsg[1]),
    'authTag': binascii.hexlify(encryptedMsg[2]),
}
print("encrypted msg:", encryptedMsgObj)

decryptedMsg = decrypt_ECC(encryptedMsg, privKeyBob, pubKeyAlice)
print("decrypted msg:", decryptedMsg)
decryptedMsgSender = decrypt_ECC_sender(encryptedMsg, privKeyAlice, pubKeyBob)
print("decrypted msg sender:", decryptedMsgSender)