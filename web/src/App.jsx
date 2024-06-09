import React, { useRef } from 'react';
import './App.css';
import Expert from './experts/Expert'
import { WiredCard, WiredButton } from 'react-wired-elements';

function App() {
  const expert = useRef(null);
  const expert2 = useRef(null);
  return (
    <div className="App">
      <header className="App-header">
        AI Multi Expert System<br/><br/>
      </header>
      <div>
        <WiredButton style={{color:'white'}} onClick={()=>{
            expert.current?.speak('Hola soy Mauricio, el ejecutivo de cuentas');
            setTimeout(()=>{
                expert2.current?.speak('Hola soy el diseñador gráfico');
            }, 2000);
        }} >Hacer que hablen</WiredButton>
        <Expert ref={expert} flipped={false}/>
        <Expert ref={expert2} flipped={false} bgColor="#000" hairColor="#964B00"/>
      </div>
    </div>
  );
}

export default App;
