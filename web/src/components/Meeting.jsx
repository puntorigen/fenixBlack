import React, { useRef, useEffect, useCallback, useState, forwardRef, useImperativeHandle } from 'react';
import { zodToJson } from '../utils/utils';

const useRefs = () => {
    const refs = useRef({});

    const register = useCallback((refName, ref) => {
        refs.current[refName] = ref;
    }, []);

    //const getRef = useCallback(refName => refs.current[refName], []);

    return [ refs, register ];
};

const Meeting = forwardRef(({ name, task, outputKey, children }, refMain) => {
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
            const onConnect = () => {            
                let payload = {
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
            const handleMessage = (event) => {
                // 3. wait for responses and update the children with the new data
                let obj = event.data;
                try {
                    obj = JSON.parse(event.data);
                } catch(e) {}
                console.log('Received data:', obj);
                // Handle the data received from the backend
                // Optionally close the websocket if the task is complete
                // if obj is string
                if (typeof obj === 'string' &&  obj === 'KEEPALIVE') { //ignore keepalive events
                } else if (obj?.action === 'server_status') {
                } else if (obj?.action === 'createTask') {
                    // dummy, update an avatar with the data (just testing)
                    if (refs.current['field-1']) {
                        refs.current['field-1'].speak(obj.data);
                    }
                } else if (obj?.action === 'improvedTask') {
                    // dummy, update an avatar with the data (just testing) 
                    if (refs.current['field-0']) {
                        refs.current['field-0'].speak(obj.data.description);
                    }
                } else if (obj?.action === 'finishedMeeting') {
                    // dummy, update an avatar with the data (just testing)
                    if (refs.current['field-0']) {
                        refs.current['field-0'].speak("The meeting was completed, check the console output for the data.");
                        let zod_schema = {};  
                        try {
                            let raw_obj = JSON.parse(obj.data.raw);
                            console.log('Raw OBJ output:', raw_obj);
                            zod_schema = schema.parse(raw_obj);
                            console.log('Schema enforced result:', zod_schema);
                        } catch(e) {
                            console.error('Schema enforcement failed:', e);
                        }
                    }
                    // 4. wait for end of meeting, convert output JSON to zod schema and return, and assign raw output to outputKey ref variable
                    if (websocketRef.current) {
                        websocketRef.current.close();
                        console.log('Meeting ended and socket closed.');
                    }
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
            {enhancedChildren}
        </div>
    );
});

export default Meeting;
