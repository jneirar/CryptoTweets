import React, { useState, useEffect } from 'react';
import myData from './privateKey.json';
import axios from 'axios';
import 'react-minimal-side-navigation/lib/ReactMinimalSideNavigation.css';
import {DashboardLayout} from "./Components/Layout";
import './App.css';
import * as functions from "./functions";
const FileSaver = require('file-saver');


function Twittercallback() {
    const API_URL = "http://localhost:5000"
    const [usuarios, setUsuarios] = useState("");
    const [data, setData] = useState({});
    const [keyDisplay, setKeyDisplay] = useState("");
    const [friendKey, setFriendKey] = useState("");
    const [friendKeyTwitter, setFriendKeyTwitter] = useState("");
    const [privateKeyVar, setPrivateKeyVar] = useState({});

    const [recibirPublicKey, setRecibirPublicKey] = useState("");

    const [tweetText, setTweetText] = useState("");
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

    const decrypt = async() =>{
        //share secret
        let tweet = tweetsCargados[0];
        let tweetID = tweet.id_str;
        let enText = tweet.full_text;
        let fromID = tweet.user.id_str;
        let tweet_nounce = "";
        let tweet_tag = "";
        let aux = {};
        console.log(tweet);
        console.log(enText);
        let prevArray = enText.split(',');
        console.log(prevArray);
        let array = new Uint8Array(prevArray);
        console.log(array);
        console.log(fromID);
        console.log(tweetID);
        const keyImported_receive = await functions.importPrivateKeyFromFile(myData);
        console.log(keyImported_receive);

        const response_leer = axios.get(`${API_URL}/get_public_key`, {params: {user_id : fromID}}).then(
            async r => {
                console.log("GET PUBLIC KEY");
                console.log(r);
                setRecibirPublicKey(r.data["public_key"]);
                aux = JSON.parse(recibirPublicKey);
                console.log(aux);
                const keyImportedFriend = await functions.importPublicKeyFromFile(aux);
                const keyShared = await functions.deriveSecretKey(keyImported_receive, keyImportedFriend);
                console.log(keyImportedFriend);
                console.log(keyShared);

                const response_dencrypt = axios.get(`${API_URL}/get_tweet_db_by_id`, {params: {tweet_id : tweetID  }}).then(
                    async res => {
                        console.log("OUTPUT");
                        console.log(res);
                        tweet_nounce = res.data.tweet[4];
                        let varNounce = new Uint8Array(tweet_nounce);
                        tweet_tag = res.data.tweet[5];
                        let varIV = new Uint8Array(tweet_tag);
                        console.log(varNounce);
                        console.log(varIV);
                        const textDecrypted = await functions.decryptData(keyShared, array, varNounce, varIV);
                    })

            }
        )
    }

    const encrypt = async() =>{
        //const keyShared = await functions.deriveSecretKey(privateKeyVar, keyPublicFriend);
        //read private key from file
        const keyImported = await functions.importPrivateKeyFromFile(myData);
        const keyImportedFriend = await functions.importPublicKeyFromFile(receiverKey);
        const keyShared = await functions.deriveSecretKey(keyImported,keyImportedFriend);
        const encryptResult = await functions.encryptData(keyShared, tweetText);
        var view = new Uint8Array(encryptResult.cipherdata);
        console.log("VIEW");
        console.log(view.toString());
        const finalText = functions.tagToString(view);
        const finalNounce = functions.tagToString(encryptResult.iv);
        const finalMac = functions.tagToString(encryptResult.tag);

        console.log("FRIEND ID");
        console.log(friendKey);
        console.log("MY ID");
        console.log(data.id);
        console.log("My Private Key");
        console.log(keyImported);
        console.log("My friend public Key");
        console.log(keyImportedFriend);

        var viewIV = new Uint8Array(encryptResult.iv);
        var viewTAG = new Uint8Array(encryptResult.tag);

        const response6 = axios.post(`${API_URL}/post_crypted_tweet`, {tweet_crypted : view.toString(), user_id_sender : data.id.toString(), user_id_receiver : friendKey.toString(), tweet_nounce : viewIV.toString(), tweet_mac : viewTAG.toString()}, {headers: {access_token: data.access_token.toString(), access_token_secret : data.access_token_secret.toString()}})
            .then(r6 =>{
                console.log(r6);
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
                                                const response2 = axios.post(`${API_URL}/create_user`, {user_username: data.username.toString(), user_id_twitter: data.user_id.toString(), user_public_key: ret.toString(), user_private_key_hashed: retPriv.toString()}).then(r=>{
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
        const response =  axios.get(`${API_URL}/get_users`, { params: {user_id : data.user_id.toString() ,access_token: data.access_token.toString(), access_token_secret : data.access_token_secret.toString()}}).then(s => {
                console.log(s);
            setFriendKey(s.data.users[0].user_id);
            setFriendKeyTwitter(s.data.users[0].user_id_twitter);
            setUsuarios("Registered Users:\n" + s.data.users[0].username + "     " + "Public Key:  " + s.data.users[0]["public_key"] );
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
        });
    }

    function escribirTweet(e){
        //Encriptamos tweet
        encrypt();

    }

    function getInfo(e){
        const response5 = axios.get(`${API_URL}/get_public_key`, { params: { user_id : friendKeyTwitter.toString()}}).then(r => {

            console.log("PUBLIC KEY SLECTED: ", r.data["public_key"]);
            setReceiverKey(JSON.parse(r.data["public_key"].toString()));
            //setFriendKey(r.data["public_key"].toString());
        });
    }

    function dencrypt(e){
        decrypt();
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
            <p>{keyDisplay}</p>
            <simpleTextLayout/>

            <div style={{paddingTop: "20px"}}></div>
            <div className={"KeyText"}>
                <div className={keyDisplay ? "col" : ""}>
                </div>
            </div>
            <button className={"ActionButton"} onClick={listUsers}>List Users</button>
            <p onClick={getInfo}>{usuarios}</p>

            <div style={{paddingTop: "20px"}}></div>
            <div>
                <button className={"ActionButton"} onClick={cargarTweet}>Cargar Tweets</button>
                <div style={{paddingTop: "20px"}}></div>
            </div>
            <div>
                <button className={"ActionButton"} onClick={dencrypt}>Descifrar Tweets</button>
                <div style={{paddingTop: "20px"}}></div>
            </div>
            <div >

                Write something
                            <br></br>
                <input
                    type="text"
                    value={tweetText}
                    onChange={(e) => setTweetText(e.target.value)}
                />
                <br></br>
                <div style={{paddingTop: "20px"}}></div>
                <button className={"ActionButton"} onClick={escribirTweet}>TWEET NOW</button>


            </div>
        </div>
    </div>
  );
}

export default Twittercallback;
