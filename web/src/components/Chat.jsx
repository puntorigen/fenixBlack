import React, { useRef, useEffect, useCallback, useState, forwardRef, useImperativeHandle } from 'react';
import styles from '@chatscope/chat-ui-kit-styles/dist/default/styles.min.css';
import { Avatar, MainContainer, ChatContainer, MessageList, Message, MessageInput, TypingIndicator, MessageGroup } from '@chatscope/chat-ui-kit-react';
import TimeAgo from 'react-timeago'

const Chat = forwardRef(({
    id = "chat",
    width = "500px",  // default width
    height = "400px",  // default height
    style = {},
    experts = {},
    messages = {},
    showThoughts = false,
    showStatus = true,
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
                setLastStatus(null);
                //setLastStatus(`${lastMessage.speaker} is typing ..`);
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
                    if (!showThoughts && message.type === 'thought') return null;
                    const sender = message.speaker;
                    const lastKey = Object.keys(messages).pop();
                    let role = message.role;
                    if (message.type === 'thought') role += ' (Thinking)';
                    let sentTime = message.time;
                    if (key === lastKey) {
                        sentTime = (<TimeAgo date={message.date} />);
                    }
                    let picture = '/fenix.png';
                    if (sender in profiles) picture = profiles[sender].picture;
                    let direction = 'incoming';
                    let avatarPosition = 'tl';
                    if (message.message.indexOf(' said]') !== -1) {
                        direction = 'outgoing';
                        avatarPosition = 'tr';
                        if (message.tool_id) {
                            if (message.tool_id === 'phone_call') {
                                picture = '/tools/phone.png';
                            }
                        }
                    }
                    // parse message for tool icons (only for incoming messages)
                    if (direction === 'incoming') {
                        if (message.message.indexOf('[phone]:') !== -1) {
                            // replace [phone]: from message with img src='/tools/phone.png' 
                            message.message = message.message.replace(/\[phone\]:/g, '<img src="/tools/phone.png" style="width:15px;height:15px;vertical-align: middle;" />');
                        } else if (message.tool_id && message.tool_id === 'phone_call') {
                            // prepend img src='/tools/phone.png' to message, only if it doesn't have an img tag already
                            if (message.message.indexOf('<img') === -1) {
                                message.message = '<img src="/tools/phone.png" style="width:15px;height:15px;vertical-align: middle;" /> ' + message.message;
                            }
                        }
                    }
                    //
                    return (
                        <MessageGroup key={'msg'+index} direction={direction} avatarPosition={avatarPosition}>
                            <Avatar src={picture} name={sender} />
                            <MessageGroup.Header style={{ color:'black' }}>{sender}&nbsp;-&nbsp;{role}</MessageGroup.Header>
                            <MessageGroup.Footer style={{ display: 'flex', justifyContent: 'flex-end' }}>{sentTime}</MessageGroup.Footer>
                            <MessageGroup.Messages style={{ textAlign:'left' }}>
                                <Message model={{
                                    //direction: "incoming",
                                    type: "custom"
                                }}>
                                    <Message.CustomContent>
                                        <div dangerouslySetInnerHTML={{ __html:message.message }}/>
                                    </Message.CustomContent>
                                </Message>
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