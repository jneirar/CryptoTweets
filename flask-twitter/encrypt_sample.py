from encrypt_functions import *

msg = b'Hola Bob, como estas?'
print("original msg:", msg)
privKeyAlice, pubKeyAlice = generate_keys()
privKeyBob, pubKeyBob = generate_keys()
first = pubKeyAlice.x
second = pubKeyAlice.y
limit = 64

print("Alice's private key:", private_key_to_string(privKeyAlice))
print("Length of Alice's private key:", len(private_key_to_string(privKeyAlice)))
print("Alice's public key:", public_key_to_string(pubKeyAlice))
print("Length of Alice's public key:", len(public_key_to_string(pubKeyAlice)))
print()
print("Bob's private key:", private_key_to_string(privKeyBob))
print("Length of Bob's private key:", len(private_key_to_string(privKeyBob)))
print("Bob's public key:", public_key_to_string(pubKeyBob))
print("Length of Bob's public key:", len(public_key_to_string(pubKeyBob)))
print()




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