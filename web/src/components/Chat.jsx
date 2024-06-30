import React, { useRef, useEffect, useCallback, useState, forwardRef, useImperativeHandle } from 'react';
import styles from '@chatscope/chat-ui-kit-styles/dist/default/styles.min.css';
import { Avatar, MainContainer, ChatContainer, MessageList, Message, MessageInput, MessageGroup } from '@chatscope/chat-ui-kit-react';

const Chat = forwardRef(({
    id = "chat",
    width = "400px",  // default width
    height = "300px",  // default height
    style = {},
    model = {},
    experts = {}
}, mainRef) => {
    const [ size, setSize ] = useState({ width, height });
    const [ profiles, setProfiles ] = useState({});

    useEffect(() => {
        const init = () => {
            if (experts) {
                let _profiles = {};
                for (let expert in experts) {
                    // remove role from key name
                    const just_name = expert.split('|')[0];
                    _profiles[just_name] = experts[expert];
                }
                console.log('profiles',_profiles,experts);
                setProfiles(_profiles);
            }
        };
        init();
    }, [experts]);

    return (profiles && Object.keys(profiles).length > 0) && (
        <center>
        <div style={{ position:"relative", height: height, width: width }}>
            <MainContainer style={{ background:'white' }}>
            <MessageGroup direction="incoming" sender="Joe" sentTime="just now" avatarPosition="tl">
                <Avatar src={profiles['Julio'].picture} name="Joe" />
                <MessageGroup.Header style={{ color:'black' }}>Julio one minute ago</MessageGroup.Header>
                <MessageGroup.Messages>
                    <Message model={{
                        message: "Hello my friend",
                        sentTime: "just now",
                        direction: "incoming",
                        sender: "Joe"
                    }}/>
                </MessageGroup.Messages>
            </MessageGroup>
            </MainContainer>
        </div>
        </center>
    )
});

export default Chat;