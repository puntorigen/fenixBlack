import React, { useRef, useEffect, useCallback, useState, forwardRef, useImperativeHandle } from 'react';
import { zodToJson,splitSentences } from '../utils/utils';

const useRefs = () => {
    const refs = useRef({});

    const register = useCallback((refName, ref) => {
        refs.current[refName] = ref;
    }, []);

    //const getRef = useCallback(refName => refs.current[refName], []);

    return [ refs, register ];
};

const Meeting = forwardRef(({ name, task, outputKey, children, onFinish }, refMain) => {
    const [refs, register] = useRefs();
    const [experts, setExperts] = useState({});
    const websocketRef = useRef(null);

    useEffect(() => {
        // Log meta information from children
        const parseChildren = () => {
            Object.keys(refs.current).forEach(refName => {
                if (refs.current[refName] && refs.current[refName].meta) {
                    const meta = refs.current[refName].meta();
                    const avatar_id = refs.current[refName].getID();  // trick to get the ID of the agent
                    if (meta.type === 'expert') {
                        meta.avatar_id = avatar_id;
                        setExperts(prev => {
                            return { ...prev, [meta.name+'|'+meta.role]: meta };
                        })
                    }
                }
            });
        }
        parseChildren();
        // Clean up WebSocket connection when component unmounts
        return () => {
            if (websocketRef.current) {
                websocketRef.current.close();
            }
        };
    }, []); // Ensure it runs whenever children change
 
    const enhancedChildren = React.Children.map(children, (child, index) =>
        React.cloneElement(child, { ...child.props, style:{ marginLeft: '20px' }, id:`field-${index}` ,ref: (ref)=>register(`field-${index}`,ref) })
    );

    const connectWebSocket = async (meetingId, onMessage, onOpen) => {
        const websocket = new WebSocket(`ws://localhost:8000/meeting/${meetingId}`);
        websocket.onopen = () => {
            console.log('WebSocket Connected');
            onOpen();  // Call the callback that handles the sending of the initial data
        };
        websocket.onerror = error => console.error('WebSocket Error: ', error);
        websocket.onmessage = onMessage;  // Set dynamically
        websocket.onclose = () => console.log('WebSocket Closed');
        websocketRef.current = websocket;
        return websocket;
    };    

    // Expose Meeting's methods to parent through ref
    useImperativeHandle(refMain, () => ({
        start: async(context,schema)=>{
            // start meeting with given context, and zod output schema
            // 1. build a JSON of the meeting info + children JSON info + zod schema JSON
            const onConnect = async() => {            
                let payload = {
                    cmd: 'create_meeting',
                    meta: {
                        context,
                        schema: zodToJson(schema),
                        name, task
                    },
                    experts
                };
                //console.log('payload',payload);
                // send to backend
                if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
                    websocketRef.current.send(JSON.stringify(payload));
                    console.log('Request sent:', payload);
                }
            }
            // 2. connect to backend via websocket and send data
            const handleMessage = async(event) => {
                // 3. wait for responses and update the children with the new data
                let obj = event.data;
                try {
                    obj = JSON.parse(event.data);
                } catch(e) {}
                // Handle the data received from the backend
                // Optionally close the websocket if the task is complete
                // if obj is string
                if (typeof obj === 'string' &&  obj === 'KEEPALIVE') { //ignore keepalive events
                    console.log('Received keepalive event.');
                } else if (obj?.action === 'server_status') {
                } else if (obj?.action === 'createTask') {
                    // dummy, update an avatar with the data (just testing)
                    console.log('Received data:', obj);
                    if (refs.current['field-1']) {
                        await refs.current['field-1'].speak(obj.data);
                    }
                } else if (obj?.action === 'improvedTask') {
                    // dummy, update an avatar with the data (just testing) 
                    console.log('Received data:', obj);
                    if (refs.current['field-0']) {
                        // split the description into an array 
                        const sentences = splitSentences(obj.data.description_first_person);
                        //console.log('sentences',sentences);
                        await refs.current['field-0'].speak(sentences);
                    }
                } else if (obj?.action === 'reportAgentSteps') {
                    // @TODO: move these conditions into the backend
                    let play = {
                        valid: false,
                        sentences: '',
                        expert_id: null,
                        tool_id: null,
                        kind: null
                    };
                    // new version
                    if (obj.expert_action && obj.expert_action.valid === true) {
                        play.valid = true;
                        play.expert_id = obj.expert_action.expert_id;
                        play.tool_id = obj.expert_action.tool_id;
                        play.kind = obj.expert_action.kind;
                        play.sentences = obj.expert_action.speak.trim();
                        // trim sentences                        
                        if (play.sentences==='') {
                            play.valid = false;
                            console.log('DEBUG: No sentences to speak, skipping obj.',obj);
                        }
                    }
                    /*
                    // iterate over obj.data array
                    for (const key in obj.data) {
                        if (obj.data[key].type === 'tool') {
                            if (obj.data[key].data?.error === false) {
                                if (obj.data[key].data.tool_id && obj.data[key].data.tool_id !== '') {
                                    // animate the avatar's tool and speak the 'log'
                                    play.valid = true;
                                    play.kind = 'tool';
                                    play.expert_id = obj.expert_id;
                                    play.tool_id = obj.data[key].data.tool_id;
                                    play.sentences.push(obj.data[key].data.log);
                                }
                            }
                        } else if (play.kind === 'kind' && obj.data[key].type === 'response' && obj.data[key].data) {
                            // this should the response of the tool
                            let lines_ = obj.data[key].data.lines.join('.');  
                            if (lines_.indexOf(`won't be used because`) !== -1 || lines_ === '') {
                                play.valid = false;
                                break;
                            }
                            // only add the lines if they are not empty and until 'Action:' appears
                            for (let i = 0; i < obj.data[key].data.lines.length; i++) {
                                if (obj.data[key].data.lines[i].indexOf('Action:') !== -1) {
                                    break;
                                }
                                play.sentences.push(obj.data[key].data.lines[i]);
                                //lines_ += ;
                            }
                        }
                    }
                    */ 
                    // only play animation if 'play.valid' is true
                    if (play.valid === true) {
                        console.log('DEBUG: TOOL DETECTED:',play,obj,refs.current[play.expert_id]);
                        if (refs.current[play.expert_id]) {
                            await refs.current[play.expert_id].play(play.tool_id);
                            await refs.current[play.expert_id].speak(play.sentences,400,150,300,async function() {
                                console.log('meeting->agent speaking done');
                                refs.current[play.expert_id].avatarSize('100%');
                                await refs.current[play.expert_id].stop();
                            });
                        }
                    }

                } else if (obj?.action === 'finishedMeeting') {
                    // dummy, update an avatar with the data (just testing)
                    // stop all animations and speak the final message
                    // iterate refs
                    for (const expert_id in refs.current) {
                        if (refs.current[expert_id].stop) {
                            await refs.current[expert_id].avatarSize('100%');
                            await refs.current[expert_id].stop();
                        } 
                    }
                    //
                    if (refs.current['field-0']) {
                        refs.current['field-0'].speak("The meeting was completed, check the console output for the data.");
                    }
                    let zod_schema = {};  
                    try {
                        zod_schema = schema.parse(obj.data);
                        console.log('Schema enforced result:', zod_schema);
                    } catch(e) {
                        console.error('Schema enforcement failed:', e);
                        console.log('Received data:', obj);
                    }
                    // 4. wait for end of meeting, convert output JSON to zod schema and return, and assign raw output to outputKey ref variable
                    if (websocketRef.current) {
                        websocketRef.current.close();
                        console.log('Meeting ended and socket closed.');
                    }
                    // 5. call onFinish callback with the zod schema enforced data
                    onFinish && onFinish(zod_schema);
                } else {
                    console.log('(unhandled) Received data:', obj);
                }
            };
            const websocket = await connectWebSocket(name, handleMessage, onConnect);
            
        },
        play: async()=>{
            // animate the meeting -> to test the experts
            const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
            Object.keys(refs.current).forEach(async(refName) => {
                if (refs.current[refName] && refs.current[refName].speak) {
                    await refs.current[refName].play('search');
                    await refs.current[refName].speak(`Hello, I am the ${refs.current[refName].meta().role}, and I'm here to help you with your task.`);
                    await sleep(4000);
                    await refs.current[refName].play('scrape');
                    await sleep(5000);
                    await refs.current[refName].avatarSize('100%');
                    await refs.current[refName].stop();
                    await sleep(5000);
                }
            }); 
        }
    }));

    return (
        <div>
            <h1 style={{ color:'#FFF'}}>Meeting</h1> 
            { task && <center><p style={{ color:'yellow', width:'500px' }}>Task: {task}</p></center> }
            {enhancedChildren}
        </div>
    );
});

export default Meeting;
