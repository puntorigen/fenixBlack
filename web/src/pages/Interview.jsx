import React, { useRef, useState, useEffect } from 'react';
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
//import { brandSchema, brochureSchema, privacyPolicy } from '../schemas';

import Meeting from '../components/Meeting';
import AccountManager from '../experts/AccountManager';
import Stakeholder from '../experts/Stakeholder';
import Designer from '../experts/Designer';

function Interview() {
    const tester = useRef(null); 
    const [testTask, setTestTask] = useState('Call the user to ask what kind of pizza does he likes and what ingredients he would like to have in it.');
    const [inMeeting, setInMeeting] = useState(false);
    const [visible, setVisible] = useState(true);
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
            await tester.current.start(
                testTask,
                null
            ); 
            setInMeeting(true); 
          }}
        >Start Meeting</WiredButton>
        <Meeting 
          name="userPreferences" 
          ref={tester} 
          task="Create a complete summary of what the user likes and prefers to have on a pizza. We'll use this info later to request a pizza to a pizzeria, so be detailed. Craft a list of questions/queries and ask the user about them in a conversation." 
          hidden={false} 
          //rules={['/rules/base.txt']}
          onDialog={(dialog)=>setDialog(dialog)} //transcription
          onFinish={(output)=>{
            console.log('meeting onFinish called',output);
            setInMeeting(false);
          }}>
          <Stakeholder user_name="Pablo" user_role="CEO" />
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

export default Interview;