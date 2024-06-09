import React, { useRef } from 'react';
import './App.css';
import Expert from './experts/Expert'
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';

function App() {
  const expert = useRef(null);
  const expert2 = useRef(null);
  return (
    <div className="App">
      <header className="App-header">
        AI Multi Expert System<br/><br/>
      </header>
      {/* 
        // brandSchema = zod.object({
        //     brand: zod.object({
        //         name: zod.string().describe('The name of the brand'),
        //         logo: zod.string().describe('The URL of the logo image'),
        //         colors: zod.object({
        //             primary: zod.string().describe('The primary color for the brand'),
        //             secondary: zod.string().describe('The secondary color for the brand'),
        //         }).describe('The main colors for the brand') ,
        //         fonts: zod.array(zod.string())
        //     }),
        //     products: zod.array(zod.object({
        //         name: zod.string(),
        //         description: zod.string(),
        //         price: zod.number(),
        //         image: zod.string(),
        //     }))
        // });)
      // info = await factory.current.start("brandBuilder", 
            " for www.xx.com",
            brandSchema
         );
      // ask the user to choose a product, or use the first one
      // brochure = await factory.current.start("brochure", 
            `using the {brand} information, design a 1 page PDF brochure for product ${info.products[0].name}`,
            zod.object({
                title: zod.string('Brochure title'),
                base64: zod.string('PDF base64')
            })
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
        <Expert ref={expert} flipped={false}/>
        <Expert ref={expert2} flipped={false} bgColor="#000" hairColor="#964B00" style={{ marginLeft: '20px' }}/>
      </div>
      <div>
    
      </div>
    </div>
  );
}

export default App;
