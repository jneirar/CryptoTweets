import React from 'react';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import TwitterCallback from "./TwitterCallback";
import HomePage from "./PAGES/Home";
import FunctionTest from './functiontest'; //new

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App/>} />
        <Route path="/twitter_auth_callback" element={<TwitterCallback/>} />{/*new*/}
          <Route path="/twitter_auth_callback" element={<TwitterCallback/>} />{/*new*/}
          <Route path="/home" element={<HomePage/>}/>{}
          <Route path="/test" element={<FunctionTest/>} />{/*new*/}
      </Routes>
    </BrowserRouter>
  </>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
