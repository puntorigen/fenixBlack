import React, { useRef, useEffect, useCallback, useState, forwardRef, useImperativeHandle } from 'react';
import styles from '@chatscope/chat-ui-kit-styles/dist/default/styles.min.css';
import { Avatar, MainContainer, ChatContainer, MessageList, Message, MessageInput, TypingIndicator, MessageGroup } from '@chatscope/chat-ui-kit-react';
import TimeAgo from 'react-timeago'
import { last } from 'lodash';

const Chat = forwardRef(({
    id = "chat",
    width = "500px",  // default width
    height = "400px",  // default height
    style = {},
    messages = {},
    experts = {}
}, mainRef) => {
    const [ size, setSize ] = useState({ width, height });
    const [ profiles, setProfiles ] = useState({});
    const [ lastStatus, setLastStatus ] = useState(null);

    useEffect(() => {
        const init = () => {
            if (experts) {
                let _profiles = {};
                for (let expert in experts) {
                    // remove role from key name
                    const just_name = expert.split('|')[0];
                    _profiles[just_name] = experts[expert];
                }
                //console.log('profiles',_profiles,experts);
                setProfiles(_profiles);
            }
        };
        init();
    }, [experts]);

    useEffect(() => {
        // get last message from messages
        if (messages && Object.keys(messages).length > 0) {
            const lastKey = Object.keys(messages).pop();
            const lastMessage = messages[lastKey];
            if (lastMessage.type === 'intro') {
                setLastStatus(null);
            } else if (lastMessage.type === 'says') {
                setLastStatus(`${lastMessage.speaker} is typing ..`);
            } else if (lastMessage.type === 'thought') {
                setLastStatus(`${lastMessage.speaker} is thinking ..`);
            }
        }
    }, [messages]);

    return (profiles && Object.keys(profiles).length > 0) && (
        <center>
        <div style={{ position:"relative", height: height, width: width }}>
            <MainContainer style={{ background:'white' }}>
            <MessageList style={{height: height }}
                autoScrollToBottom={true}
                autoScrollToBottomOnMount={true}
                typingIndicator={lastStatus && <TypingIndicator content={lastStatus} />}>
            { messages && Object.keys(messages).length > 0 && Object.keys(messages).map((key, index) => {
                    const message = messages[key];
                    const sender = message.speaker;
                    const lastKey = Object.keys(messages).pop();
                    let sentTime = message.time;
                    if (key === lastKey) {
                        sentTime = (<TimeAgo date={message.date} />);
                    }
                    let picture = '/fenix.png';
                    if (sender in profiles) picture = profiles[sender].picture;
                    return (
                        <MessageGroup key={'msg'+index} direction={"incoming"} avatarPosition="tl">
                            <Avatar src={picture} name={sender} />
                            <MessageGroup.Header style={{ color:'black' }}>{sender}&nbsp;-&nbsp;{message.role}&nbsp;-&nbsp;{sentTime}</MessageGroup.Header>
                            <MessageGroup.Messages style={{ textAlign:'left' }}>
                                <Message color='#f00' model={{
                                    message: message.message,
                                    direction: "incoming"
                                }}/>
                            </MessageGroup.Messages>
                        </MessageGroup>
                    )
                }
            )}
            </MessageList>
            </MainContainer>
        </div>
        </center>
    )
});

export default Chat;