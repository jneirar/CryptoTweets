import axios from 'axios';
import './App.css';

function App() {
  const API_URL = "http://localhost:5000"

  const initTwitterAuth = () => { //new
    axios.request({ //new
      method: "post", //new
      url: `${API_URL}/auth_twitter`, //new
      data: {callback_url: "http://localhost:3000/twitter_auth_callback"} //new
  }).then((response) => { //new

    const { data } = response; //new
    window.location.href = data.redirect_url; //new
  }).catch((error) => { //new
      console.log(error); //new
  }); //new
  } //new

  return (
    <div className="App">
      <div style={{paddingTop: "400px"}}>
        <button onClick={initTwitterAuth}>Connect To Twitter</button> {/*new*/}
      </div>
    </div>
  );
}

export default App;