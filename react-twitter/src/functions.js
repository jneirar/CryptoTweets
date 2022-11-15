const FileSaver = require('file-saver');

// function to generate a pair of keys
export const generateKeyPair = async () => {
    const keyPair = await window.crypto.subtle.generateKey(
        {
            name: "ECDH",
            namedCurve: "P-256", //can be "P-256", "P-384", or "P-521"
        },
        true, //whether the key is extractable (i.e. can be used in exportKey)
        ["deriveKey", "deriveBits"] //can be any combination of "deriveKey" and "deriveBits"
    )
        .then(function (key) {
            //returns a keypair object
            return key;
        })
        .catch(function (err) {
            console.error(err);
        });
    return keyPair;
}


export const savePrivateKeyToFile = async (key) => {
    const exportedKey = await window.crypto.subtle.exportKey(
        "jwk", //can be "jwk" or "raw"
        key
    )
        .then(function (keydata) {
            //returns the exported key data
            return keydata;
        })
        .catch(function (err) {
            console.error(err);
        });

    // save exportedKey to a file
    const blob = new Blob([JSON.stringify(exportedKey)], { type: "text/plain;charset=utf-8" });
    FileSaver.saveAs(blob, "privateKey.json");
}

export const saveKeyToFile = async (key) => {
    const exportedPrivateKey = await window.crypto.subtle.exportKey(
        "jwk", //can be "jwk" or "raw"
        key.privateKey
    )
        .then(function (keydata) {
            //returns the exported key data
            return keydata;
        })
        .catch(function (err) {
            console.error(err);
        });
    
    const exportedPublicKey = await window.crypto.subtle.exportKey(
        "jwk", //can be "jwk" or "raw"
        key.publicKey
    )
        .then(function (keydata) {
            //returns the exported key data
            return keydata;
        })
        .catch(function (err) {
            console.error(err);
        });
        
    // make a json object with both keys
    const keyPair = {
        privateKey: exportedPrivateKey,
        publicKey: exportedPublicKey
    }

    // save keyPair to a file
    const blob = new Blob([JSON.stringify(keyPair)], { type: "text/plain;charset=utf-8" });
    FileSaver.saveAs(blob, "keys.json");
}


export const importPrivateKeyFromFile = async (jsonData) => {
    const importedKey = await window.crypto.subtle.importKey(
        "jwk", //can be "jwk" or "raw"
        jsonData, //this is an example j
        {   //these are the algorithm options
            name: "ECDH",
            namedCurve: "P-256", //can be "P-256", "P-384", or "P-521"
        },
        true, //whether the key is extractable (i.e. can be used in exportKey)
        ["deriveKey", "deriveBits"] //can be any combination of "deriveKey" and "deriveBits"
    )
        .then(function (key) {
            //returns the symmetric key
            return key;
        })
        .catch(function (err) {
            console.error(err);
        });
    return importedKey;
}

export const importKeyPairFromFile = async (jsonData) => {
    
    const importedPrivateKey = await window.crypto.subtle.importKey(
        "jwk", //can be "jwk" or "raw"
        jsonData['privateKey'], //this is an example j
        {   //these are the algorithm options
            name: "ECDH",
            namedCurve: "P-256", //can be "P-256", "P-384", or "P-521"
        },
        true, //whether the key is extractable (i.e. can be used in exportKey)
        ["deriveKey", "deriveBits"] //can be any combination of "deriveKey" and "deriveBits"
    )
        .then(function (key) {
            //returns the symmetric key
            return key;
        })
        .catch(function (err) {
            console.error(err);
        });

    const importedPublicKey = await window.crypto.subtle.importKey(
        "jwk", //can be "jwk" or "raw"
        jsonData['publicKey'], //this is an example j
        {   //these are the algorithm options
            name: "ECDH",
            namedCurve: "P-256", //can be "P-256", "P-384", or "P-521"
        },
        true, //whether the key is extractable (i.e. can be used in exportKey)
        [] //can be any combination of "deriveKey" and "deriveBits"
    )
        .then(function (key) {
            //returns the symmetric key
            return key;
        })
        .catch(function (err) {
            console.error(err);
        });

    return {
        privateKey: importedPrivateKey,
        publicKey: importedPublicKey}
}


export const extractData = async (key) => {
    const exportedKey = await window.crypto.subtle.exportKey(
        "jwk",
        key
    )
        .then(function (keydata) {
            return keydata;
        })
        .catch(function (err) {
            console.error(err);
        });
    return exportedKey;
}

export const deriveSecretKey = async (privateKey, publicKey) => {
    const secret = await window.crypto.subtle.deriveKey(
        {
            name: "ECDH",
            namedCurve: "P-256",
            public: publicKey,
        },
        privateKey,
        {
            name: "AES-GCM",
            length: 256
        },
        true,
        ["encrypt", "decrypt"]
    )
        .then(function (keydata) {
            //returns the derived bits as an ArrayBuffer
            return keydata;
        })
        .catch(function (err) {
            console.error(err);
        });
    return secret;
}

export const encryptData = async (key, data) => {
    const dataBuffer = new TextEncoder().encode(data);
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const tag = window.crypto.getRandomValues(new Uint8Array(16));
    const encryptedData = await window.crypto.subtle.encrypt(
        {
            name: "AES-GCM",
            iv: iv,
            additionalData: tag,
            tagLength: 128
        },
        key,
        dataBuffer
    )
    .then(function (encrypted) {
            //returns an ArrayBuffer containing the encrypted data
            return encrypted;
        }
        )
    .catch(function (err) {
            console.log("Encryption error");
            console.error(err);
        }
        );
    return {
        cipherdata: encryptedData,
        iv: iv,
        tag: tag
    };
}

export const decryptData = async (key, cipherdata, iv, tag) => {
    const decryptedDataBuffer = await window.crypto.subtle.decrypt(
        {
            name: "AES-GCM",
            iv: iv,
            additionalData: tag,
            tagLength: 128
        },
        key,
        cipherdata
    )
        .then(function (decrypted) {
            return decrypted;
        })
        .catch(function (err) {
            console.log("Decryption error");
            console.error(err);
        });
    const decryptedData = new TextDecoder().decode(decryptedDataBuffer);
    return decryptedData;
}

export const tagToString = (tag) => {
    return String.fromCharCode.apply(null, tag);
}