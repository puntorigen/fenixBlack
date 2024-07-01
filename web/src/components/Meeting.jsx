import React, { useRef, useEffect, useCallback, useState, forwardRef, useImperativeHandle } from 'react';
import { zodToJson,splitSentences,getBrowserFingerprint,encryptData } from '../utils/utils';
import { useWindowSize } from "@uidotdev/usehooks";
import { motion, AnimatePresence } from 'framer-motion';

const useRefs = () => {
    const refs = useRef({});

    const register = useCallback((refName, ref) => {
        refs.current[refName] = ref;
    }, []);

    //const getRef = useCallback(refName => refs.current[refName], []);

    return [ refs, register ];
};

const Meeting = forwardRef(({ name, task, rules=[], outputKey, children, onInit, onFinish, onError, onDialog, hidden = false }, refMain) => {
    const [refs, register] = useRefs();
    const expertSaidHi = useRef({});
    const launchedInit = useRef({});
    const [isVisible, setVisible] = useState(!hidden);
    const [enhancedChildren, setEnhancedChildren] = useState([]);
    const [experts, setExperts] = useState({});
    const websocketRef = useRef(null);
    const windowSize = useWindowSize();
    const [combinedRules, setCombinedRules] = useState(''); // concatentated rules for the experts
    const [inProgress, setInProgress] = useState(false); 
    const [settings_, setSettings_] = useState({}); // all the settings here are sent encrypted
    const [sessionKey, setSessionKey] = useState(''); // session key for secure communication with backend
    const [fingerprint, setFingerprint] = useState(''); // unique user fingerprint (or userid)
    const [transcript, setTranscript] = useState([]);
    const addTranscript = (speaker,message,type='thought',role='coordinator') => {
        let obj = { speaker, role, type, message };
        obj.date = new Date();
        obj.time = obj.date.toLocaleTimeString();
        if (type === 'thought') {
            obj.full = `${obj.time} [${obj.role}] ${obj.speaker}: (THINKS: ${obj.message})`;
        } else if (type === 'intro') {
            obj.full = `${obj.time} [INTRO]: ${obj.message}`;
        } else {
            obj.full = `${obj.time} [${obj.role}] ${obj.speaker}: ${obj.message}`;
        }
        setTranscript(prev => [...prev, obj]);
    };

    const itemVariants = {
        hidden: { x: 50, opacity: 0 },
        visible: i => ({ x: 0, opacity: 1, transition: { delay: i * 0.5, type: 'spring', stiffness: 120 } }),
        exit: i => ({
            x: -100,  // Move to the left
            opacity: 0,
            transition: {
                delay: i * 0.7,  // Apply staggered delay based on index
                type: 'spring',
                stiffness: 120
                //duration: 1.5,
                //ease: 'easeInOut'
            }
        })
    };

    const variants = {
        hidden: { opacity: 0, scale: 0.95 },
        visible: { opacity: 1, scale: 1 }
    };
    
    const parseChildren = () => { 
        Object.keys(refs.current).forEach((refName) => {
            if (refs.current[refName] && refs.current[refName].meta) {
                const meta = refs.current[refName].meta();
                const avatar_id = refs.current[refName].getID();  // trick to get the ID of the agent
                if (meta.type === 'expert') {
                    if (!meta.avatar_id) meta.avatar_id = avatar_id;
                    if (!(`${meta.name}|${meta.role}` in experts)) {
                        let selfie_bgcolor = meta.avatar.bgColor;
                        // if selfie_bgcolor is not a valid hex color, set it to a default
                        if (selfie_bgcolor.length !== 7 || selfie_bgcolor.length !== 4) {
                            selfie_bgcolor = '#6BD9E9';
                        }
                        refs.current[refName].selfie(selfie_bgcolor).then((picture)=>{
                            meta.picture = picture;
                            setExperts(prev => {
                                return { ...prev, [meta.name+'|'+meta.role]: meta };
                            });
                        });
                    }
                }
            }
        });
    };

    useEffect(() => {
        // load the urls from the rules array, and combine them as a single enumerated string
        // for the experts to use them as part of their backstories
        const downloadRule = async function(uri) {
            const response = await fetch(uri);
            const text = await response.text();
            return text;
        }
        const process = async() => {
            let rules_ = ''; 
            const text2rules = (text, idx=0) => {
                let rules__ = '';
                let currentIdx = idx;
                // break the text into breaklines, remove the int. at the begining and add to rules_
                for (const line of text.split('\n')) {
                    // remove the initial number of the line if it exists and if the line is not empty
                    if (line.trim().length > 0) {
                        // remove the initial number of the line if it exists
                        const parts = line.split('. ');
                        if (parts.length > 1) {
                            rules__ += `${currentIdx}. ${parts[1]}\n`;
                        } else {
                            rules__ += `${currentIdx}. ${line}\n`;
                        }
                        currentIdx += 1;
                    }
                }
                return { text:rules__, last_idx:currentIdx };
            }
            // loop and count index
            if (rules && Array.isArray(rules) && rules.length > 0) {
                let realIdx = 0;
                for (let idx=0; idx < rules.length; idx++) {
                    const rule = rules[idx];
                    if (rule.startsWith('http')) {
                        const text = await downloadRule(rule);
                        let rules_obj = text2rules(text, realIdx+1);
                        realIdx = rules_obj.last_idx;
                        rules_ += rules_obj.text;
                    } else { 
                        const text = await downloadRule(rule);
                        let rules_obj = text2rules(text, realIdx+1);
                        realIdx = rules_obj.last_idx;
                        rules_ += rules_obj.text;
                    }
                }
                setCombinedRules(rules_);
            }
        }
        process();
    }, [rules])

    useEffect(() => {
        // Log meta information from children
        //const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
        const init = async() => {
            const result = await getBrowserFingerprint();
            setFingerprint(result);
        };        
        setTranscript([]);
        addTranscript('Fenix',`Hi my name is Fenix and I'm the Meeting Coordinator. My goal is to 'help the team coordinate tasks between team members and query customer data'.`,'intro','Meeting Coordinator');
        // prepare the children nodes
        parseChildren();
        init();
        // Clean up WebSocket connection when component unmounts
        return () => {
            if (websocketRef.current) { 
                websocketRef.current.close();
            }
        };
    }, []); // Ensure it runs whenever children change

    useEffect(()=> {
        const run = () => {        
            const newEnhancedChildren = React.Children.map(children, (child, index) =>
                <motion.div
                    variants={itemVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    custom={index}
                    style={{ marginLeft: '20px' }}
                >
                    {React.cloneElement(child, { ...child.props, style:{ }, id:`field-${index}` ,ref: (ref)=>register(`field-${index}`,ref) })}
                </motion.div>
            );
            setEnhancedChildren(newEnhancedChildren);
            if (children && children.length && children.length != Object.keys(experts).length) {
                //console.log('reparsing children',children.length,Object.keys(experts).length)
                parseChildren();
            } else if (enhancedChildren && enhancedChildren.length && enhancedChildren.length != Object.keys(experts).length) {
                parseChildren();
            }
            //console.log('enhancedChildren regenerated!',experts,newEnhancedChildren);
        };
        run();
    }, [children])

    const connectWebSocket = async (meetingId, onMessage, onOpen) => {
        const websocket = new WebSocket(`ws://localhost:8000/meeting/${meetingId}`);
        websocket.onopen = () => {
            console.log('WebSocket Connected');
            onOpen();  // Call the callback that handles the sending of the initial data
        };
        websocket.onerror = error => console.error('WebSocket Error: ', error);
        websocket.onmessage = onMessage;  // Set dynamically
        websocket.onclose = async() => {
            if (inProgress && inProgress === true) {
                // there was an error because the connection was closed before the meeting ended
                onError && onError('Connection closed before the meeting ended.');
                // stop all avatar animations
                try {
                    for (const expert_id in refs.current) {
                        refs.current[expert_id].avatarSize('100%');
                        await refs.current[expert_id].stop();
                    }
                } catch(err) {}
                setInProgress(false); 
            } else {
                console.log('WebSocket Closed');
            }
        }
        websocketRef.current = websocket;
        return websocket;
    };

    // adjust size depending on the number of expert childrens
    useEffect(() => {
        console.log('adjusting experts box size ..')
        let size = 300; // used to adjust by percentage to fit width of screen
        let screenWidth = windowSize.width * 0.9; // 90% of full width
        if (Object.keys(experts).length > 0) {
            size = screenWidth/Object.keys(experts).length;
        }
        // limit the max and min sizes
        if (size > 300) size = 300; 
        if (size < 180) size = 180; 
        for (const expert_id in refs.current) {
            // iterate the experts and set the size
            if (refs.current[expert_id] && refs.current[expert_id].setSize) {
                //console.log('setting expert size box to',size+'px',size+'px')
                refs.current[expert_id].setSize(size+'px',size+'px');
            }
            // say welcome message if the expert has not said hi
            if (!expertSaidHi.current[expert_id]) {
                const meta = refs.current[expert_id].meta();
                addTranscript(meta.name,`Hi my name is ${meta.name} and I'm the ${meta.role} in this meeting. My goal is to help in '${meta.goal}'.`,'intro',meta.role);
                expertSaidHi.current[expert_id] = true;
            }
        }
        //
        if (Object.keys(experts).length > 0 && !launchedInit.current[`num_experts${Object.keys(experts).length}`]) {
            launchedInit.current[`num_experts${Object.keys(experts).length}`] = true;
            onInit && onInit(experts);
        }
        //console.log('debug experts',experts);
        //
    }, [experts, windowSize.width]);

    useEffect(() => {
        // emit the transcript to the parent
        onDialog && onDialog(transcript);
    },[transcript])

    const sentToBackend = async(payload) => {
        if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
            websocketRef.current.send(JSON.stringify(payload));
            console.log('Request sent:', payload);
        }
    }; 

    useEffect(() => {
        console.log('Updated settings:', settings_);
    }, [settings_]);

    // Expose Meeting's methods to parent through ref
    useImperativeHandle(refMain, () => ({ 
        show: () => setVisible(true),
        hide: () => setVisible(false),
        getTranscript: () => transcript,    // for parent to get the transcript
        start: async(context,schema,settings)=>{
            // start meeting with given context, and zod output schema
            // 1. build a JSON of the meeting info + children JSON info + zod schema JSON
            if (settings) { 
                setSettings_((prev)=>{ return { ...prev, ...settings } });
            } 
            const onConnect = async() => {
                // init connection by sending a request for a session key
                // exchange with server the fingerprint and get the session_key, so we can encrypt the settings
                // request session_key to server
                await sentToBackend({
                    cmd: 'req_session_key',
                    fingerprint 
                });
            }
            // 2. connect to backend via websocket and send data
            const handleMessage = async(event) => {
                // 3. wait for responses and update the children with the new data
                const dJSON = require('dirty-json');
                let obj = event.data;
                try {
                    obj = JSON.parse(event.data);
                } catch(e) {}
                // Handle the data received from the backend
                // Optionally close the websocket if the task is complete
                // if obj is string
                if (typeof obj === 'string' &&  obj === 'KEEPALIVE') { //ignore keepalive events
                    console.log('Received keepalive event.');
                } else if (obj?.action === 'session_key') {
                    // when the server sends the session key, we can now encrypt data
                    // request meeting launch
                    let payload = {
                        cmd: 'create_meeting',
                        meta: {
                            context,
                            name, task, rules: combinedRules 
                        }, 
                        experts,
                        settings: encryptData(settings?settings:{}, obj.key),
                        fingerprint 
                    }; 
                    if (schema) { // the schema is optional
                        payload.meta.schema = zodToJson(schema);
                    }
                    setSessionKey(obj.key); // we need this key to encrypt the data before sending it
                    addTranscript('Fenix',`The user has given us the following task: '${payload.meta.task}'`,'says','Meeting Coordinator');
                    await sentToBackend(payload);

                } else if (obj?.action === 'server_status') {
                } else if (obj?.action === 'creating_expert') {
                    // in_progress when creating expert
                    // in_progress false when expert created (after it has studied)
                    if (obj.in_progress === true) {
                        //console.log('Creating expert:', obj);
                        // say Hi if expert has things to study 
                        if (refs.current[obj.expert_id] && refs.current[obj.expert_id].speak) {
                            const meta_expert = refs.current[obj.expert_id].meta();
                            if (meta_expert.study && meta_expert.study.length > 0) {
                                await refs.current[obj.expert_id].speak(`Hello, my name is ${meta_expert.name}, I'm the ${meta_expert.role}, and I am studying the material you gave me.`);
                            }
                        }
                    } else {
                        //console.log('Expert created:', obj);
                        if (refs.current[obj.expert_id] && refs.current[obj.expert_id].speak) {
                            const meta_expert = refs.current[obj.expert_id].meta();
                            if (meta_expert.study && meta_expert.study.length > 0) {
                                await refs.current[obj.expert_id].speak(`I'm ready to start the meeting.`);
                            } else {
                                await refs.current[obj.expert_id].speak(`Hello, my name is ${meta_expert.name}, I'm the ${meta_expert.role}, and I'm here to help you with your task.`);
                            }
                        }
                    }
                } else if (obj?.action === 'createTask') {
                    // dummy, update an avatar with the data (just testing)
                    console.log('Received data:', obj);
                    if (refs.current['field-1'] && refs.current['field-1'].speak) {
                        await refs.current['field-1'].speak(obj.data);
                    } 
                } else if (obj?.action === 'improvedTask') {
                    // gets the improved version of the user task that's going to be used
                    setInProgress(true);
                    addTranscript('Fenix',`${obj.data.description_first_person}. ${obj.data.expected_output}'.`,'thought','Meeting Coordinator');
                    console.log('Received data:', obj);
                    if (refs.current['field-0']) {
                        // split the description into an array
                        const meta1 = refs.current['field-0'].meta(); 
                        addTranscript(meta1.name,obj.data.description_first_person,'says',meta1.role);
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
                    if (obj.expert_action) {
                        play.valid = obj.expert_action.valid;
                        play.expert_id = obj.expert_action.expert_id;
                        play.tool_id = obj.expert_action?.tool_id;
                        play.kind = obj.expert_action?.kind;
                        play.sentences = obj.expert_action.speak;
                        try {
                            play.sentences = play.sentences.trim();
                        } catch(err) {}
                        if (play.sentences==='') {
                            play.valid = false;
                            console.log('DEBUG: EMPTY SENTENCES:',obj);
                        } 
                    }
                    // only play animation if 'play.valid' is true
                    if (play.valid === true && play.kind === 'tool') {
                        console.log('DEBUG: TOOL DETECTED:',obj);
                        if (refs.current[play.expert_id]) {
                            await refs.current[play.expert_id].play(play.tool_id);
                            await refs.current[play.expert_id].speak(play.sentences,400,150,300,async function() {
                                console.log('meeting->agent speaking done'); 
                                refs.current[play.expert_id].avatarSize('100%');
                                await refs.current[play.expert_id].stop();
                            });
                            const meta_expert = refs.current[play.expert_id].meta();
                            addTranscript(meta_expert.name,play.sentences,'says',meta_expert.role);
                        }
                    } else if (play.valid === true && play.kind === 'thought') {
                        console.log('DEBUG: NEW THOUGHT DETECTED:',obj);
                        if (refs.current[play.expert_id]) { 
                            await refs.current[play.expert_id].play(play.tool_id);
                            await refs.current[play.expert_id].speak(`(${play.sentences})`,400,150,1000,async function() {
                                console.log('meeting->agent speaking done (thought)'); 
                                refs.current[play.expert_id].avatarSize('100%'); 
                                await refs.current[play.expert_id].stop();
                            });
                            const meta_expert = refs.current[play.expert_id].meta();
                            addTranscript(meta_expert.name,play.sentences,'thought',meta_expert.role);
                        } 
                    } else if (play.kind === 'tool') {
                        console.log('TOOL NOT USED', obj);
                    }

                } else if (obj?.action === 'raw_output') {
                    // this is the unstructured end of the meeting
                    // stop all animations and speak the final message
                    // iterate refs
                    let manager_expert_id = null;
                    for (const expert_id in refs.current) {
                        if (refs.current[expert_id].stop) {
                            await refs.current[expert_id].avatarSize('100%');
                            await refs.current[expert_id].stop();
                        }
                        // make the first avatar 'speak' the final result (TODO should be a manager)
                        // loop through the refs and find the first 'manager' (role)
                        const meta_expert = refs.current[expert_id].meta();
                        if (meta_expert.role && meta_expert.role.toLowerCase().indexOf('manager')!=-1) {
                            manager_expert_id = expert_id;
                        }
                    }

                } else if (obj?.action === 'finishedMeeting') {
                    // get the first manager of the team meeting
                    let manager_expert_id = null;
                    for (const expert_id in refs.current) {
                        const meta_expert = refs.current[expert_id].meta();
                        if (meta_expert.role && meta_expert.role.toLowerCase().indexOf('manager')!=-1) {
                            manager_expert_id = expert_id;
                        }
                    }
                    // if there's no manager on the team, make the first avatar 'speak' the final result
                    if (!manager_expert_id) {
                        manager_expert_id = 'field-0';
                    }
                    const meta_expert = refs.current[manager_expert_id].meta();
                    addTranscript(meta_expert.name,'The meeting has ended, thank you everyone.','says',meta_expert.role);
                    if (obj.final_report) {
                        addTranscript(meta_expert.name,'This is the result of our meeting: '+obj.final_report,'says',meta_expert.role);
                    } else {
                        addTranscript(meta_expert.name,'This is the result of our meeting: '+obj.data,'says',meta_expert.role);
                    }
                    refs.current[manager_expert_id].speak("The meeting was completed, check the console output for the data.");

                    // final STRUCTURED output of the meeting
                    let zod_schema = obj.data;  
                    if (schema) {
                        try {
                            zod_schema = schema.parse(obj.data);
                            //console.log('Schema enforced result:', zod_schema);
                        } catch(e) {
                            try {
                                zod_schema = dJSON.parse(obj.data);
                                //console.log('Schema enforced2 result:', zod_schema);
                            } catch(e2) { 
                                zod_schema = obj.data;
                                console.error('Schema enforcement failed:', e);
                                console.log('Received data:', zod_schema);
                            } 
                        } 
                    } else {
                        console.log('Meeting without schema. Final received data:', zod_schema);
                    }
                    // 4. wait for end of meeting, convert output JSON to zod schema and return, and assign raw output to outputKey ref variable
                    setInProgress(false);
                    if (websocketRef.current) {
                        websocketRef.current.close();
                        console.log('Meeting ended and socket closed.');
                    }
                    // 5. call onFinish callback with the zod schema enforced data
                    onFinish && onFinish({ data:zod_schema, metrics:obj.metrics });
                } else {
                    console.log('(unhandled) Received data:', obj);
                }
            };
            const websocket = await connectWebSocket(name, handleMessage, onConnect);
            
        },
        play: async()=>{
            // animate the meeting -> to test the experts
            const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
            // animate the meeting -> to test the experts
            for (const refName of Object.keys(refs.current)) {
                const currentRef = refs.current[refName];
                if (currentRef && currentRef.speak) {
                    await currentRef.play('search');
                    const role = currentRef.meta().role;
                    await currentRef.speak(`Hello, I am the ${role}, and I'm here to help you with your task.`);
                    
                    await sleep(4000);
                    await currentRef.play('scrape');
                    
                    await sleep(5000);
                    await currentRef.avatarSize('100%');
                    await currentRef.stop();

                    await sleep(5000);
                }
            }
        }
    }));

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial="hidden"
                    animate="visible"
                    exit="hidden"
                    variants={variants}
                    transition={{ duration: 0.5 }}
                >
                    <h1 style={{ color:'#FFF'}}>Meeting</h1> 
                    { task && <center><p style={{ color:'yellow', width:'500px' }}>Task: {task}</p></center> }
                    <div style={{ 
                            display: 'flex', 
                            flexDirection: 'row', 
                            justifyContent: 'center',
                            alignItems: 'center',
                            flexWrap: 'wrap',
                            width: '100%'
                        }}>
                        {enhancedChildren}
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
});

export default Meeting;
