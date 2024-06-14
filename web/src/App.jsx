import React, { useRef } from 'react';
import './App.css';
import Meeting from './components/Meeting';
import AccountManager from './experts/AccountManager';
import Designer from './experts/Designer';
import Lawyer from './experts/Lawyer';
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
import { brandSchema, brochureSchema, privacyPolicy } from './schemas';
import { tools } from './experts/constants';

function App() {
  const meetingBrand = useRef(null);
  const meetingPrivacy = useRef(null);
  return (
    <div className="App">
      <header className="App-header">
        AI Multi Expert System<br/><br/>
      </header>
      {/* 
      // info = await factory.current.start("brandBuilder", 
            " for www.xx.com",
            brandSchema
         );
      // ask the user to choose a product, or use the first one
      // brochure = await factory.current.start("brochure", 
            `using the {brand} information, design a 1 page PDF brochure for product ${info.products[0].name}`,
            brochureSchema
        );

      <Factory industry="marketing" ref={factory}>
        <WhiteBoard type={"thought"} for="single|all" ref={thinkingBoard}/> // shows a mindmap of the thought or output process
        <Meeting name="brandBuilder" ref={meetingBrand} task="research the products, services and build the design brand guidelines" outputKey="brand">
            <WhiteBoard type={"output"} /> //shows a mindmap of the overall work output
            <AccountManager age={37} gender={"male"} name={"Mauricio"} />
            <Designer gender={"female"} name={"Marta"} />
        </Meeting>
        <Meeting name="brochure" ref={meetingBrochure} objective="Design a PDF brochure" outputKey="brochure">
            <AccountManager name={"Mauricio"} /> //each 'name' has memory context history
            <PrintDesigner gender={"male"} name={"Christian"} /> // expert at creating designs for print
            <PDFBuilder gender={"male"} name={"Pablo"} /> // (dev like) expert at creating PDFs using weasyPrint in the back
            <Copywriter name={"Rodrigo"} />
            <ProductManager name={"Rodrigo"} />
            <Reviewer name={"Leo"} task={"Checks the brochure for errors in grammar, spelling, and punctuation."} />
        </Meeting>
      </Factory>
      */}
      <div>
      </div>
      <div>
        {/*
        
        <Meeting 
          name="privacyPolicy" 
          ref={meetingPrivacy} 
          task="scan and review the privacy policy and check if it's inline with GDPR" 
          outputKey="brand"
          onFinish={(output)=>{
            console.log('meeting onFinish called',output);
          }}>
          <AccountManager name="Mauricio1" />
          <Designer />
          <Lawyer />
        </Meeting>
        */}

        <Meeting 
          name="brandBuilder" 
          ref={meetingBrand} 
          task="research what does the company do, their colors, fonts, their products and prices, and build a design brand guideline report" 
          outputKey="brand"
          onFinish={(output)=>{
            console.log('meeting onFinish called',output);
          }}>
          <AccountManager name="Mauricio" />
          <Designer />
        </Meeting>
      </div>
      <div>
      <button onClick={async()=>{
        //await privacyPolicy.current.start('Create a review for propertyradar.com',privacyPolicy);
        await meetingBrand.current.start('Create brand guidelines for propertyradar.com',brandSchema);
        //meetingBrand.current.play();
      }}>Start Meeting</button>
        </div>
    </div>
  );
}

export default App;
