import React, { useRef, useState, useEffect } from 'react';
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
import { brandSchema, brochureSchema, privacyPolicy } from '../schemas';

import Meeting from '../components/Meeting';
import AccountManager from '../experts/AccountManager';
import Lawyer from '../experts/Lawyer';

function PrivacyExample2() {
    const meetingPrivacy = useRef(null); 
    const [testTask, setTestTask] = useState('Check www.enecon.com');
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
        <div>
        <WiredButton 
          style={{marginTop:20, color:'yellowgreen' }}
          disabled={inMeeting}
          onClick={async()=>{ 
            if (visible) {
                await meetingPrivacy.current.hide();
                setVisible(false);
            } else {
                await meetingPrivacy.current.show();
                setVisible(true);
            }
          }}
        >{visible===false ? ('Show'):('Hide')} Meeting</WiredButton>
        </div>
        
        <Meeting 
          name="privacyPolicy" 
          ref={meetingPrivacy} 
          task="scan and review the privacy policy and check if it's inline with GDPR" 
          outputKey="gdpr"
          hidden={true} 
          //rules={['/rules/base.txt']}
          onDialog={(dialog)=>setDialog(dialog)}
          onFinish={(output)=>{
            console.log('meeting onFinish called',output);
            setInMeeting(false);
          }}>
          <AccountManager name="Mauricio" />
          <Lawyer study={ //learns the given data before starting the meeting
            ['https://ico.org.uk/media/for-organisations/guide-to-the-general-data-protection-regulation-gdpr-1-0.pdf']
          } />
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

export default PrivacyExample2;