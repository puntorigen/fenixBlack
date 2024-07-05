import React, { useRef, useState } from 'react';
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
import { brandSchema, brochureSchema, privacyPolicy } from '../schemas';
import Chat from '../components/Chat';

import Meeting from '../components/Meeting';
import AccountManager from '../experts/AccountManager';
import Lawyer from '../experts/Lawyer';

function PrivacyExample() {
    const meetingPrivacy = useRef(null); 
    const [testTask, setTestTask] = useState('Check www.enecon.com');
    const [inMeeting, setInMeeting] = useState(false);
    const [visible, setVisible] = useState(true);
    const [dialog, setDialog] = useState([]);
    const [avatars, setAvatars] = useState({});
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
                privacyPolicy
            );
            setInMeeting(true); 
          }}
        >Start Meeting</WiredButton>
        
        <Meeting 
          name="privacyPolicy" 
          ref={meetingPrivacy} 
          task="scan and review the privacy policy and check if it's inline with GDPR" 
          outputKey="gdpr"
          //rules={['/rules/base.txt']}
          onDialog={(dialog)=>setDialog(dialog)}
          onInit={(experts)=>{
            // avatar would hold an object with the avatar's name as the key and some metadata (like picture) as the value
            //console.log('interview experts',experts);
            setAvatars(experts);
          }}
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
            <>
            <Chat experts={avatars} messages={dialog} showThoughts={false}/>
            <br/><br/>
            </>
        )}
        </>
    );
}

export default PrivacyExample;