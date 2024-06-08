import React, { useRef } from 'react';
import logo from './logo.svg';
import './App.css';
import { AccountManager } from './avatars/AccountManager';
import { Designer } from './avatars/Designer';

function App() {
  const accountManager = useRef(new AccountManager({ clippyAgent: 'Peedy' })).current;
  const designer = useRef(new Designer({ clippyAgent: 'Rocky' })).current;
  return (
    <div className="App">
      <header className="App-header">
        <accountManager.AgentComponent/>
        <designer.AgentComponent/>
        <img src={logo} className="App-logo" alt="logo" />
        <button onClick={async()=>{
          const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
          accountManager.stop();
          designer.stop();

          accountManager.hello();
          accountManager.moveTo(100,100);
          await sleep(7000);
          //await sleep(4000);
          designer.show();
          designer.moveTo(200,130);
          designer.say("Hola soy el diseñador, cómo estas?");
          accountManager.say("Hola diseñador, soy el ejecutivo de cuentas.");
        }}>Show</button>
      </header>
    </div>
  );
}

export default App;
