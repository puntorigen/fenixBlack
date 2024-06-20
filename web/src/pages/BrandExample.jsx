import React, { useRef, useState } from 'react';
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
import { brandSchema, brochureSchema, privacyPolicy } from '../schemas';
import { tools } from '../experts/constants';

import Meeting from '../components/Meeting';
import AccountManager from '../experts/AccountManager';
import Designer from '../experts/Designer';
import Lawyer from '../experts/Lawyer';
import ResearchAnalyst from '../experts/ResearchAnalyst';
import LeadMarketAnalyst from '../experts/Marketing/LeadMarketAnalyst';

function BrandExample() {
    const meetingBrand = useRef(null);
    const [testTask, setTestTask] = useState('Create brand guidelines for www.enecon.com');
    const [inMeeting, setInMeeting] = useState(false);
    const [dialog, setDialog] = useState([]);
    return (
        <>
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
            let settings = {
              env: {
                // set your own keys here -> they'll be sent encrypted to the backend
                OPENAI_API_KEY: '', // for the experts to work
                SERPER_API_KEY: '', // for searching the internet
                PINECONE_API_KEY: '', // for using it as the vectorDB
              } 
            };
            settings = {};
            await meetingBrand.current.start(testTask,brandSchema,settings);
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
      </>
    );
}

export default BrandExample;