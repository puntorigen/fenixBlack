import React, { useRef, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
import './App.css';

import HomePage from './pages/HomePage';
import BrandExample from './pages/BrandExample';
import PrivacyExample from './pages/PrivacyExample';
import PrivacyExample2 from './pages/PrivacyExample2';
import CreateNewWebPage from './pages/CreateNewWebPage';

function NavigationMenu() {
  let navigate = useNavigate();

  return (
      <nav>
          <WiredButton style={{ color:'cyan' }} elevation={2} onClick={()=>navigate('/')}>Home</WiredButton>
          <WiredButton style={{ color:'yellow', paddingLeft:'15px' }} elevation={2} onClick={()=>navigate('/brand')}>Brand Example</WiredButton>
          <WiredButton style={{ color:'yellow', paddingLeft:'15px' }} elevation={2} onClick={()=>navigate('/privacy')}>Privacy Example</WiredButton>
          <WiredButton style={{ color:'orange', paddingLeft:'15px' }} elevation={2} onClick={()=>navigate('/website')}>Create Website</WiredButton>
      </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="App">
        <div className='App-header'>
          <h1 style={{ color:'yellowgreen' }}>Fenix-Black Multi-Agent UI Framework</h1>
        </div>
        <NavigationMenu/>
        <Routes>
          <Route path="/" element={<HomePage />} exact />
          <Route path="/brand" element={<BrandExample />} />
          <Route path="/privacy" element={<PrivacyExample />} />
          <Route path="/website" element={<CreateNewWebPage />} />
        </Routes>
      </div>
    </Router>
  );
} 

export default App;
