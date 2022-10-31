import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Twittercallback() {
    const API_URL = "http://localhost:5000"

    const [data, setData] = useState({});
    
    useEffect(() => {
        //pick params and send api request to get final user data
        const path = window.location.href;
        if (path.includes("?")){
            const query = path.split("?")[1];
            let _params = query.split("&").map(x =>  x.split("="));
            _params = { oauth_token: _params[0][1], oauth_verifier: _params[1][1] };
            getUserInfo(_params);
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

    return (
        <div className="App">
        <div style={{paddingTop: "200px"}}>
            <h2>Hello, {data.username}!</h2>
        </div>
    </div>
  );
}

export default Twittercallback;