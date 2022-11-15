import React from 'react';
import * as functions from './functions';

function FunctionTest() {
    const ButtonFunc = async () => {
        // generate key pair
        const keyAlice = await functions.generateKeyPair();
        const keyBob = await functions.generateKeyPair();

        // generate shared secret
        const derived11 = await functions.deriveSecretKey(keyAlice.privateKey, keyBob.publicKey);
        const derived22 = await functions.deriveSecretKey(keyBob.privateKey, keyAlice.publicKey);

        const derived11data = await functions.extractData(derived11);
        const derived22data = await functions.extractData(derived22);

        // derived1 == derived2
        console.log("derived11data.k: ", derived11data.k);
        console.log("derived22data.k: ", derived22data.k);

        // save private key to a file
        //functions.savePrivateKeyToFile(keyAlice.privateKey);
        functions.saveKeyToFile(keyAlice);
        console.log("key saved: ", keyAlice.privateKey);
        console.log("data key saved: ", await functions.extractData(keyAlice.privateKey));
    }

    const handleChange = e => {
        const fileReader = new FileReader();
        if (e.target.files.length === 0) {
            console.log("No file");
            return;
        }
        fileReader.readAsText(e.target.files[0], "UTF-8");
        fileReader.onload = async e => {
            // read private key
            /*const keyPrivateAlice = await functions.importPrivateKeyFromFile(JSON.parse(e.target.result));
            console.log("key loaded: ", keyPrivateAlice);
            console.log("data key loaded: ", await functions.extractData(keyPrivateAlice));*/

            // read key pair
            const keyAliceImported = await functions.importKeyPairFromFile(JSON.parse(e.target.result));

            // bob key pair
            const keyBob = await functions.generateKeyPair();
            
            // secret with privateAlice and publicBob
            const keyShared = await functions.deriveSecretKey(keyAliceImported.privateKey, keyBob.publicKey);
            
            const text = "Hola mundo";
            const encryptResult = await functions.encryptData(keyShared, text);

            const keyShared2 = await functions.deriveSecretKey(keyBob.privateKey, keyAliceImported.publicKey);
            const textDecrypted = await functions.decryptData(keyShared2, encryptResult.cipherdata, encryptResult.iv, encryptResult.tag);
            console.log(textDecrypted);
        };
    };

    return (
        <div className="App">
        <div style={{paddingTop: "200px"}}>
            <h2>Hello</h2>
            <button onClick={ButtonFunc}>Click me</button>
            <br/>
            <br/>
            <input onChange={handleChange} type="file" accept='.json' multiple/>
        </div>
    </div>
  );
}

export default FunctionTest;