import React, { useRef, useState, useEffect } from 'react';
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
import { brandSchema, brochureSchema, privacyPolicy } from '../schemas';

import Meeting from '../components/Meeting';
import AccountManager from '../experts/AccountManager';
import Stakeholder from '../experts/Stakeholder';
import Designer from '../experts/Designer';

function CreateNewWebPage() {
    const meetingPrivacy = useRef(null); 
    const [testTask, setTestTask] = useState('Create a 3 page website for a real state Property Company, based in Santiago, Chile, specialized in selling beach houses in the coast of the country.');
    const [inMeeting, setInMeeting] = useState(false);
    const [visible, setVisible] = useState(false);
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
            await meetingPrivacy.current.start(
                testTask,
                null
            ); 
            setInMeeting(true); 
          }}
        >Start Meeting</WiredButton>
        <Meeting 
          name="privacyPolicy" 
          ref={meetingPrivacy} 
          task="scan and review the privacy policy and check if it's inline with GDPR" 
          outputKey="gdpr"
          hidden={false} 
          //rules={['/rules/base.txt']}
          onDialog={(dialog)=>setDialog(dialog)}
          onFinish={(output)=>{
            console.log('meeting onFinish called',output);
            setInMeeting(false);
          }}>
          <AccountManager name="Mauricio" />
          <Stakeholder user_name="Pablo" user_role="CEO" />
          <Designer study={[
            //'https://blog.logrocket.com/ux-design/30-design-techniques/',
            'https://assets.ctfassets.net/uha7v3hw004j/4FuCRjBFe4mtOBU236eNyZ/5bdbf5f91949a26138bf6d6c1ed23dcc/ColorPaletteGuide_2020_HighContrast.pdf',
            //'https://cdn2.hubspot.net/hubfs/53/How%20to%20Create%20a%20Brand%20Style%20Guide%20-%20HubSpot%20%26%20Venngage%20%5BEBOOK%20+%20TEMPLATES%5D.pdf'
          ]} />
        </Meeting>
        {visible===true && (
            <WiredCard elevation={2} style={{marginBottom:100, color:'white', textAlign:'left', width:'80%' }}>
                <h2>Meeting Transcription</h2>
                <span style={{ fontFamily:'sans-serif' }}>
                    {dialog && dialog.map((d,i)=><p key={i}>{d.full}</p>)}
                </span>
            </WiredCard>
        )}
        </>
    );
}

export default CreateNewWebPage;