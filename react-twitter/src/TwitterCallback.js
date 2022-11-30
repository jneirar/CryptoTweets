import React, { useState, useEffect } from 'react';
import myData from './privateKey.json';
import myDataRec from './privateKeySUEL.json';
import axios from 'axios';
import './App.css';
import * as functions from "./functions";
const FileSaver = require('file-saver');

function ab2str(buf) {
    return String.fromCharCode.apply(null, new Int8Array(buf));
}
function str2ab(str) {
    var buf = new ArrayBuffer(str.length*1); // 2 bytes for each char
    var bufView = new Int8Array(buf);
    for (var i=0, strLen=str.length; i < strLen; i++) {
        bufView[i] = str.charCodeAt(i);
    }
    return buf;
}

function stringToHash(string) {

    var hash = 0;

    if (string.length == 0) return hash;

    for (let i = 0; i < string.length; i++) {
        let char = string.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }

    return hash;
}




function Twittercallback() {
    const API_URL = "http://localhost:5000"
    const [tweetText, setTweetText] = useState("");
    const [usuarios, setUsuarios] = useState("");
    const [data, setData] = useState({});
    const [keyDisplay, setKeyDisplay] = useState("");
    const [friendKey, setFriendKey] = useState("");
    const [friendKeyTwitter, setFriendKeyTwitter] = useState("");
    const [privateKeyVar, setPrivateKeyVar] = useState({});
    const [tweetDecripted, setTweetDecripted] = useState("");

    const [textito, setTextito] = useState("");

    const [recibirPublicKey, setRecibirPublicKey] = useState("");

    const [tweetTexto, setTweetTexto] = useState("");
    const [tweetTexto2, setTweetTexto2] = useState("");
    const [indexTweet, setIndexTweet] = useState(0);
    const [toID, setToID] = useState("");
    const [receiverKey, setReceiverKey] = useState({});

    const [tweetsCargados, setTweetsCargados] = useState([]);
    
    useEffect(() => {
        //pick params and send api request to get final user data
        const path = window.location.href;
        if (path.includes("?")){
            const query = path.split("?")[1];
            let _params = query.split("&").map(x =>  x.split("="));
            _params = { oauth_token: _params[0][1], oauth_verifier: _params[1][1] };
            getUserInfo(_params);
            console.log(_params);
        }
    }, []);

    const getUserInfo = (params) => {
        axios.get( `${API_URL}/twitter_auth_callback`,
                { params: params })
                .then(d => {
                    console.log(d);
                    setData(d.data);
                });
    }

    const test = async() =>{
        const private1 = await functions.importPrivateKeyFromFile(myData);
        const private2 = await functions.importPrivateKeyFromFile(myDataRec);
        const public2request =  axios.get(`${API_URL}/get_public_key`, {params: {user_id : "1596050405640867841"}}).then(
            async function llaves(outputKey) {
                setRecibirPublicKey(outputKey.data["public_key"]);
                let aux = JSON.parse(recibirPublicKey);
                const public2 = await functions.importPublicKeyFromFile(aux);
                const public1request = axios.get(`${API_URL}/get_public_key`, {params: {user_id : "1169792879813779456"}}).then(
                    async function llavemia(outputkey2){
                        let public1temp = outputkey2.data["public_key"];
                        let public1 = await functions.importPublicKeyFromFile(JSON.parse(public1temp));
                        const keyShared = await functions.deriveSecretKey(private1, public2);
                        const keyShared2 = await functions.deriveSecretKey(private2, public1);
                        const derived11data = await functions.extractData(keyShared);
                        const derived22data = await functions.extractData(keyShared2);
                        console.log("derived11data.k: ", derived11data.k);
                        console.log("derived22data.k: ", derived22data.k);
                    }
                )
            }
        )
    }

    const decrypt = async(e) =>{
        const fileReader = new FileReader();
        if (e.target.files.length === 0) {
            console.log("No file");
            return;
        }
        fileReader.readAsText(e.target.files[0], "UTF-8");
        fileReader.onload = async e => {
            const keyImported_receive = await functions.importPrivateKeyFromFile(JSON.parse(e.target.result));
            let tweet = tweetsCargados[indexTweet];
            let tweetID = tweet.id_str;
            let enText = tweet.full_text;
            let fromID = tweet.user.id_str;
            let tweet_nounce = "";
            let tweet_tag = "";
            let aux = {};
            const response_leer = axios.get(`${API_URL}/get_public_key`, {params: {user_id : fromID}}).then(
                async r => {
                    setRecibirPublicKey(r.data["public_key"]);
                    console.log(recibirPublicKey);
                    aux = JSON.parse(recibirPublicKey);
                    const keyImportedFriend = await functions.importPublicKeyFromFile(aux);
                    const keyShared = await functions.deriveSecretKey(keyImported_receive, keyImportedFriend);
                    const derived11data = await functions.extractData(keyShared);
                    console.log("KEY SHARED", derived11data.k);
                    console.log(keyImported_receive);
                    console.log(keyImportedFriend);
                    console.log(keyShared);

                    const response_dencrypt = axios.get(`${API_URL}/get_tweet_db_by_id`, {params: {tweet_id : tweetID  }}).then(
                        async res => {
                            let array = res.data.tweet[7];
                            tweet_nounce = res.data.tweet[4];
                            let varNounce = str2ab(tweet_nounce);
                            tweet_tag = res.data.tweet[5];
                            let varMAC = str2ab(tweet_tag);

                            console.log(res);
                            console.log("text: ", str2ab(array))
                            console.log("keyShared", keyShared);
                            console.log("VAR NOUNCE", varNounce);
                            console.log("varMAC", varMAC);
                            const textDecrypted = await functions.decryptData(keyShared, str2ab(array), varNounce, varMAC);
                            console.log(("text original ", textDecrypted));
                            setTweetDecripted("Texto decifrado: "+ textDecrypted);

                            const updateresponsepost = axios.post(`${API_URL}/update_not_readed_tweet`, {tweet_id_twitter : res.data.tweet[1]}).then(
                                r =>{console.log(r);
                                    if(indexTweet == 0){
                                        setTweetTexto("");
                                    }else{
                                        setTweetTexto2("");
                                    }
                                    }
                            )
                        })
                }
            )
        }

        //share secret



    }

    const encrypt = async () =>{
        //const keyShared = await functions.deriveSecretKey(privateKeyVar, keyPublicFriend);
        //read private key from file
        const keyImported = await functions.importPrivateKeyFromFile(myData);
        const keyImportedFriend = await functions.importPublicKeyFromFile(receiverKey);
        const keyShared = await functions.deriveSecretKey(keyImported,keyImportedFriend);
        const derived11data = await functions.extractData(keyShared);
        console.log("KEY SHARED", derived11data.k);
        const encryptResult = await functions.encryptData(keyShared, tweetText);

        let textiton = ab2str(encryptResult.iv);
        let texts = str2ab(textiton);

        let textiton2 = ab2str(encryptResult.tag);
        let texts2 = str2ab(textiton2);

        const response6 = axios.post(`${API_URL}/post_crypted_tweet`, {tweet_crypted : ab2str(encryptResult.cipherdata), user_id_sender : data.id.toString(), user_id_receiver : friendKey.toString(), tweet_nounce : ab2str(encryptResult.iv), tweet_mac : ab2str(encryptResult.tag)}, {headers: {access_token: data.access_token.toString(), access_token_secret : data.access_token_secret.toString()}})
            .then(r6 =>{
                console.log(r6);
                console.log("keyShared ", keyShared);
                console.log("text: ", encryptResult.cipherdata);
                console.log("nounce: ", encryptResult.iv);
                console.log("mac; ", encryptResult.tag );
            });
    }

    const managePublicKey = async(key) => {
        const exportedKey = await window.crypto.subtle.exportKey(
            "jwk", //can be "jwk" or "raw"
            key.publicKey
        ).then(function (keydata) {
                //returns the exported key data
                return keydata;
            }
        ).catch(function (err) {
            console.error(err);
        });
        setKeyDisplay(JSON.stringify(exportedKey) );
        return JSON.stringify(exportedKey);
    }

    const managePrivateKey = async(key) => {


        const exportedKey = await window.crypto.subtle.exportKey(
            "jwk", //can be "jwk" or "raw"
            key.privateKey
        ).then(function (keydata) {
                //returns the exported key data
                return keydata;
            }
        ).catch(function (err) {
            console.error(err);
        });


        // save exportedKey to a file
        const blob = new Blob([JSON.stringify(exportedKey)], { type: "text/plain;charset=utf-8" });
        FileSaver.saveAs(blob, "privateKey.json");


        return JSON.stringify(exportedKey);
    }

    function CheckUsers(e) {

            const response = axios.get( `${API_URL}/check_user`,
                { params: {user_id_twitter : data.user_id }})
                .then(d => {
                    if(d.data.user_exists === false){
                        const new_keys = functions.generateKeyPair().then(
                            function saveAll(keydata){
                                managePublicKey(keydata).then(
                                    function savePublic(ret){
                                        managePrivateKey(keydata).then(
                                            function savePrivate(retPriv){


                                                const hash = stringToHash(retPriv.toString());
                                                const response2 = axios.post(`${API_URL}/create_user`, {user_username: data.username.toString(), user_id_twitter: data.user_id.toString(), user_public_key: ret.toString(), user_private_key_hashed: hash}).then(r=>{
                                                    console.log(r);
                                                });
                                                setKeyDisplay(ret);
                                                setPrivateKeyVar(retPriv);
                                                data.user_id = d.data.user_id_twitter;
                                                data.id = d.data.user_id;
                                            }
                                        );
                                    }
                                );
                            }
                        );
                    }else{
                        //Save session data
                        data.user_id = d.data.user_id_twitter;
                        data.id = d.data.user_id;
                        console.log(data);
                    }
                });
    }


    function listUsers(e){
        const response =  axios.get(`${API_URL}/get_users`, { params: {user_id : data.user_id.toString() ,access_token: data.access_token.toString(), access_token_secret : data.access_token_secret.toString()}}).then(async s => {
                console.log(s);
                setFriendKey(s.data.users[0].user_id);
                setFriendKeyTwitter(s.data.users[0].user_id_twitter);
                const p = await functions.importPublicKeyFromFile((JSON.parse(s.data.users[0]["public_key"])));
                const derived22data = await functions.extractData(p);
                setUsuarios(s.data.users[0].username);
            }
        )
    }

    function myForm(){
        return (
            <form>
                <label>Enter your name:
                    <input type="text" />
                </label>
            </form>
        )
    }

    function cargarTweet(e){

        const response3 = axios.get(`${API_URL}/get_not_readed_tweets`, { params: {user_id : data.id.toString()}, headers: {access_token : data.access_token.toString(), access_token_secret : data.access_token_secret.toString()} }).then(r => {

            console.log(r);
            setTweetsCargados(r.data.tweets);
            console.log(tweetsCargados);
            setTweetTexto("1.- De: "+ r.data.tweets[0]["user"]["name"] + "   Text: " + r.data.tweets[0]["full_text"]);
            if(r.data.tweets_number > 1){
                setTweetTexto2("2.- De: "+ r.data.tweets[1]["user"]["name"] + "   Text: " + r.data.tweets[1]["full_text"]);
            }
        });
    }

    function escribirTweet(e){
        //Encriptamos tweet
        const fileReader = new FileReader();
        if (e.target.files.length === 0) {
            console.log("No file");
            return;
        }
        fileReader.readAsText(e.target.files[0], "UTF-8");
        fileReader.onload = async e => {
            const keyImported = await functions.importPrivateKeyFromFile(JSON.parse(e.target.result));
            const keyImportedFriend = await functions.importPublicKeyFromFile(receiverKey);
            const keyShared = await functions.deriveSecretKey(keyImported,keyImportedFriend);
            const derived11data = await functions.extractData(keyShared);
            console.log("KEY SHARED", derived11data.k);
            const encryptResult = await functions.encryptData(keyShared, tweetText);

            let textiton = ab2str(encryptResult.iv);
            let texts = str2ab(textiton);

            let textiton2 = ab2str(encryptResult.tag);
            let texts2 = str2ab(textiton2);

            const response6 = axios.post(`${API_URL}/post_crypted_tweet`, {tweet_crypted : ab2str(encryptResult.cipherdata), user_id_sender : data.id.toString(), user_id_receiver : friendKey.toString(), tweet_nounce : ab2str(encryptResult.iv), tweet_mac : ab2str(encryptResult.tag)}, {headers: {access_token: data.access_token.toString(), access_token_secret : data.access_token_secret.toString()}})
                .then(r6 =>{
                    console.log(r6);
                    console.log("keyShared ", keyShared);
                    console.log("text: ", encryptResult.cipherdata);
                    console.log("nounce: ", encryptResult.iv);
                    console.log("mac; ", encryptResult.tag );
                });


        }

        //encrypt();

    }

    function getInfo(e){
        const response5 = axios.get(`${API_URL}/get_public_key`, { params: { user_id : friendKeyTwitter.toString()}}).then(r => {

            console.log("PUBLIC KEY SLECTED: ", r.data["public_key"]);
            setReceiverKey(JSON.parse(r.data["public_key"].toString()));
            //setFriendKey(r.data["public_key"].toString());
            setTextito("Usuario seleccionado");
        });
    }

    function dencrypt(e){
        decrypt(e);
    }

    function testKey(){
        test();
    }

    function clear(){
        setKeyDisplay("");
        setTextito("");
        setTweetTexto("");
        setUsuarios("");
        setTweetDecripted("");
    }

    function set0(){
        setIndexTweet(0);
        console.log("index : ", indexTweet);
    }

    function set1(){
        setIndexTweet(1);
        console.log("index : ", indexTweet);
    }


    return (
    <div>
        <div className="App">
        <div style={{paddingTop: "10px"}}>
            <h2 style={{fontFamily: "monospace", color: "white", fontSize: "xx-large"}}>Hello, {data.username}!</h2>
        </div>



    </div>

        <div style={{backgroundColor: "#fff6ed", paddingTop:"5%", paddingBottom:"100%"}}>

            <button className={"ActionButton"} onClick={CheckUsers}>Generate Keys</button>
            <p style={{paddingLeft: "35px"}}>{keyDisplay}</p>
            <simpleTextLayout/>

            <div style={{paddingTop: "40pxpx"}}></div>
            <div className={"KeyText"}>
                <div className={keyDisplay ? "col" : ""}>
                </div>
            </div>
            <button className={"ActionButton"}  style={{marginTop: "35px"}} onClick={listUsers}>List Users</button>
            <p  style={{paddingLeft: "35px"}} onClick={getInfo}>{usuarios}</p>
            <p style={{paddingLeft: "40px"}} >{textito}</p>

            <div style={{paddingTop: "20px"}}></div>
            <div>
                <button className={"ActionButton"} onClick={cargarTweet}>Cargar Tweets</button>
                <div style={{paddingTop: "20px"}}></div>
                <p style={{paddingLeft: "35px", marginBottom: "40px"}} onClick={set0} >{tweetTexto}</p>
                <p style={{paddingLeft: "35px", marginBottom: "40px"}} onClick={set1} >{tweetTexto2}</p>
            </div>
            <div className={"ActionButton"}>
                <label htmlFor="myfile" >Select your private key for access to tweet:         </label>
                <input id="myfile"  onChange={dencrypt} type="file" accept='.json' multiple />
                <div style={{paddingBottom: "0px"}}></div>
            </div>
            <p style={{paddingLeft: "35px"}}>{tweetDecripted}</p>
            <div style={{ paddingTop:"30px"}}>
                    <div style={{paddingLeft: "30px"}} >Write tweet and choose private key</div>


                <input style={{marginLeft: "30px", paddingBottom: "30px", paddingRight: "60px"}}
                    type="text"
                    value={tweetText}
                    onChange={(e) => setTweetText(e.target.value)}
                />
                <br></br>
                <div style={{paddingTop: "10px"}}></div>
                <div className={"ActionButton"} >
                    <label htmlFor="myfile" >Select your private key for writing a tweet:         </label>
                    <input onChange={escribirTweet} type="file" accept='.json' multiple/>
                </div>



            </div>

            <button style={{marginTop: "20px"}} className={"ActionButton"} onClick={clear}>CLEAR ALL</button>
        </div>
    </div>
  );
}

export default Twittercallback;
