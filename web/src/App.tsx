import React, { useRef } from 'react';
import logo from './logo.svg';
import './App.css';
import { AccountManager } from './avatars/AccountManager';
import { Designer } from './avatars/Designer';

function App() {
  const accountManager = useRef(new AccountManager({ clippyAgent: 'Clippy' })).current;
  const designer = useRef(new Designer({ clippyAgent: 'Links' })).current;
  return (
    <div className="App">
      <header className="App-header">
        <accountManager.AgentComponent/>
        <designer.AgentComponent/>
        <img src={logo} className="App-logo" alt="logo" />
        <button onClick={()=>{
          accountManager.stop();
          designer.stop();

          accountManager.show();
          accountManager.moveTo(100,100);
          accountManager.lookTo(300,130);
          accountManager.say("Hola diseñador, soy el ejecutivo de cuentas.");

          designer.show();
          designer.moveTo(300,130);
          //designer.wait(2000);
          designer.say("Hola soy el diseñador, cómo estas?");
        }}>Show</button>
      </header>
    </div>
  );
}

export default App;
