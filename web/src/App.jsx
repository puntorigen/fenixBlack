import React, { useRef } from 'react';
import './App.css';
import Expert from './experts/Expert'
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
import { brandSchema, brochureSchema } from './schemas';
import { zodToJson } from './utils/utils';

function App() {
    const expert = useRef(null);
    const expert2 = useRef(null);

    const test = zodToJson(brandSchema);
    console.log('test zod to json',test);

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
        <WhiteBoard type={"output"} for="single|all" ref={outputBoard}/> // shows a mindmap of the overall work output
        <Meeting name="brandBuilder" ref={meetingBrand} task="research the products, services and build the design brand guidelines" outputKey="brand">
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
        <Expert ref={expert}/>
        <Expert ref={expert2} bgColor="#000" hairColor="#964B00" style={{ marginLeft: '20px' }}/>
      </div>
      <div>
        <button onClick={async()=>{
            expert2.current.speak("Hello, my name is Expert 2. I am a nice avatar expert. This is a much longer string of text so to test how it is displayed. Hello, my name is Expert 2. I am a nice avatar expert. This is a much longer string of text so to test how it is displayed.");
            expert.current.speak("Searching websites for more information.",300,500);
            expert.current.avatarSize('25%','#29465B');
            await expert.current.play('searching');
            setTimeout(async() => {
                //expert.current.lookRight();
                expert2.current.lookLeft();
                expert.current.avatarSize('40%');
                expert.current.speak("Reading the contents ..",340,700);
                await expert.current.play('analyzing','#FFFFFF',true);
                setTimeout(async() => {
                    expert.current.avatarSize('100%');
                }, 5000);
            }, 3000);
        }}>Test</button>
      </div>
    </div>
  );
}

export default App;
