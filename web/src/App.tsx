import React, { useRef } from 'react';
import logo from './logo.svg';
import './App.css';
import { AccountManager } from './avatars/AccountManager';
import { Designer } from './avatars/Designer';
import Expert from './experts/Expert'

interface ExpertActions {
  speak: (message: string) => void;
}


function App() {
  const accountManager = useRef(new AccountManager({ clippyAgent: 'Merlin' })).current;
  const designer = useRef(new Designer({ clippyAgent: 'Links' })).current;
  const expert = useRef<ExpertActions | null>(null);
  return (
    <div className="App">
      <header className="App-header">
        <accountManager.AgentComponent/>
        <designer.AgentComponent/>
        <Expert ref={expert}/>
        <button onClick={()=>{
          expert.current?.speak('Hola soy el experto en React, cómo estas?');
          /*
          accountManager.stop();
          designer.stop();

          accountManager.show();
          designer.show(); 
          console.log('accountManager animations',accountManager.animations());
          designer.play('Greeting');
          designer.play('Thinking');
          designer.moveTo(300,130);
          designer.play('Explain');
          designer.moveTo(400,130);
          designer.play('EmptyTrash');
          designer.moveTo(500,130);
          designer.play('IdleButterFly');
          designer.moveTo(300,200);
          designer.play('IdleButterFly');
          
          accountManager.moveTo(100,100);
          accountManager.play('Processing');
          accountManager.play('Pleased');
          accountManager.play('Writing');
          accountManager.moveTo(800,100);
          accountManager.lookTo(300,130);
          accountManager.play('GetAttention');
          accountManager.say("Hola diseñador, soy el ejecutivo de cuentas.");

          //designer.wait(2000);
          designer.say("Hola soy el diseñador, cómo estas?");
          */
        }}>Show</button>
      </header>
    </div>
  );
}

export default App;
