import React, { useRef, useState } from 'react';
import './App.css';
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
import { brandSchema, brochureSchema, privacyPolicy } from './schemas';
import { tools } from './experts/constants';

import Meeting from './components/Meeting';
import AccountManager from './experts/AccountManager';
import Designer from './experts/Designer';
import Lawyer from './experts/Lawyer';
import ResearchAnalyst from './experts/ResearchAnalyst';
import LeadMarketAnalyst from './experts/Marketing/LeadMarketAnalyst';

function App() {
  const meetingBrand = useRef(null);
  const meetingPrivacy = useRef(null);
  const [testTask, setTestTask] = useState('Create brand guidelines for www.enecon.com');
  const [inMeeting, setInMeeting] = useState(false);
  const [dialog, setDialog] = useState([]);
  return (
      /* 
      <header className="App-header">
        AI Multi Expert System<br/><br/>
      </header>
      // info = await factory.current.start("brandBuilder", 
            " for www.xx.com",
            brandSchema
         );
      // ask the user to choose a product, or use the first one
      // brochure = await factory.current.start("brochure", 
            `using the {brand} information, design a 1 page PDF brochure for product ${info.products[0].name}`,
            brochureSchema
        );

      <Factory industry="marketing" ref={factory} flow="brandBuilder->brochure->brochurePDF" onFinish={()=>{}}>
        <WhiteBoard type={"thought"} for="single|all" ref={thinkingBoard}/> // shows a mindmap of the whole factory progress
        <Meeting name="brandBuilder" ref={meetingBrand} task="research the products, services and build the design brand guidelines" outputKey="brand">
            <WhiteBoard type={"output"} /> //shows a mindmap of the overall work output
            <AccountManager age={37} gender={"male"} name={"Mauricio"} />
            <Designer gender={"female"} name={"Marta"} />
        </Meeting>
        <Meeting name="brochure" ref={meetingBrochure} task="Create the material for a PDF brochure" outputKey="brochure">
            <AccountManager name={"Mauricio"} /> //each 'name' has memory context history
            <PrintDesigner gender={"male"} name={"Christian"} /> // expert at creating designs for print
            <PDFBuilder gender={"male"} name={"Pablo"} /> // (dev like) expert at creating PDFs using weasyPrint in the back
            <Copywriter name={"Rodrigo"} />
            <ProductManager name={"Rodrigo"} />
            <Reviewer name={"Leo"} task={"Checks the brochure for errors in grammar, spelling, and punctuation."} />
        </Meeting>
        <BrochurePDF name="brochurePDF" ref={brochurePDF} output="" /> // this takes the result from the previous step as input, and creates the PDF file as base64
      </Factory>

      <div>
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
          <Lawyer study={ //learns the given data before starting the meeting
            ['https://ico.org.uk/media/for-organisations/guide-to-the-general-data-protection-regulation-gdpr-1-0.pdf']
          } />
        </Meeting> 
        </div>
        */
        <div className="App">
          <div className='App-header'>
            <h1 style={{ color:'yellowgreen' }}>AI Multi Expert System</h1>
          </div>
        <WiredInput 
          placeholder="Test Task" 
          value={testTask}
          style={{width:'50%'}} 
          onChange={(e)=>setTestTask(e.target.value)} />
        <WiredButton 
          style={{marginTop:20, color:'yellowgreen' }}
          disabled={inMeeting}
          onClick={async()=>{
            //await privacyPolicy.current.start('Create a review for propertyradar.com',privacyPolicy);
            setInMeeting(true);
            await meetingBrand.current.start(testTask,brandSchema);
            //meetingBrand.current.play();
          }}
        >Start Meeting</WiredButton>

        <Meeting 
          name="brandBuilder" 
          ref={meetingBrand} 
          task="design a brand guideline report with their recommended hex colors usage, fonts faces and families, and build a complete design brand guideline that can be used in creating future products." 
          outputKey="brand"
          rules={['/rules/base.txt']} //url of text rules all experts need to follow (content is appended to the backstory of each expert)
          //study={[]} things that all experts need to know in order to start the meeting
          onDialog={(dialog)=>setDialog(dialog)}
          onError={(error)=>{
            console.log('meeting finished due to an error',error);
            setInMeeting(false);
          }} 
          onFinish={(output)=>{
            console.log('meeting onFinish called',output);
            setInMeeting(false);
          }}> 
          <AccountManager name="Mauricio" />
          <ResearchAnalyst /> 
          <Designer study={[
            'https://blog.logrocket.com/ux-design/30-design-techniques/',
            'https://assets.ctfassets.net/uha7v3hw004j/4FuCRjBFe4mtOBU236eNyZ/5bdbf5f91949a26138bf6d6c1ed23dcc/ColorPaletteGuide_2020_HighContrast.pdf',
            'https://cdn2.hubspot.net/hubfs/53/How%20to%20Create%20a%20Brand%20Style%20Guide%20-%20HubSpot%20%26%20Venngage%20%5BEBOOK%20+%20TEMPLATES%5D.pdf'
          ]} /> 
          <LeadMarketAnalyst name="Julio" />
        </Meeting>
        <WiredCard elevation={2} style={{marginBottom:100, color:'white', textAlign:'left', width:'80%' }}>
        <h2>Meeting Transcription</h2>
        <span style={{ fontFamily:'sans-serif' }}>
          {dialog && dialog.map((d,i)=><p key={i}>{d.full}</p>)}
        </span>
        </WiredCard> 
      </div>
  );
}

export default App;
