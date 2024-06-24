import React, { forwardRef, useRef, useEffect, useState, useImperativeHandle } from 'react';
import Puppet from '../components/Puppet';

const Agent = forwardRef(({
    id = "agent",
    width = "300px",  // default width
    height = "300px",  // default height
    style = {},
    meta = {},
    onSpeakEnd,
}, ref) => {
    const puppetRef = useRef();
    const [ size, setSize ] = useState({ width, height });

    const setup = () => {
        // Example: set up Puppet based on Agent's props like age and gender
        if (puppetRef.current) {
            //puppetRef.current.setAge(age);
            //puppetRef.current.setGender(gender);
        }
    };

    // Expose Puppet's methods to Agent's parent through ref
    useImperativeHandle(ref, () => ({
        // Inherit Puppet methods
        ...puppetRef.current,
        // Custom methods
        getID: ()=>id,
        meta: () => ({...{  
            // default personality
            personality: `Always use 'I' instead of 'You', use easy to understand terms, don't use exagerated words, and be straightfoward on the tasks you are going to perform.`,            
            max_execution_time: 60*5,   // 5 minutes
            max_num_iterations: 7       // 7 iterations; 25 default, but less is cheaper
        }, ...meta }), 
        setSize: (width, height) => setSize({ width, height }),
        play: async(tool='search',bgcolor=meta.avatar.bgColor || '#6BD9E9',textDelay=2000) => {
            if (puppetRef.current) {
                if (tool in meta.tools) {
                    let animKey = Object.keys(meta.tools[tool])[0]; // searching
                    let text = meta.tools[tool][animKey];
                    let extra = {};
                    if (animKey.indexOf(':') !== -1) { 
                        extra = { tint: animKey.split(':')[1] };
                        animKey = animKey.split(':')[0];
                    } 
                    await puppetRef.current.play(animKey,{ bgcolor, ...extra },true);
                    puppetRef.current.avatarSize('30%','#29465B');
                    await puppetRef.current.speak(text,400,150,200,async()=>{
                        console.log('agent speaking done');
                        puppetRef.current.avatarSize('100%');
                    }); 
                }
            } 
        },
        json: () => {
            // builds a JSON representation for the Meeting component
            let resp = { ...meta,
            };
            return JSON.stringify(resp);
        }
    }));

    useEffect(() => {
        setup(); // Set up Puppet when Agent is mounted
    }, []);

    return (
        <Puppet
            ref={puppetRef}
            label={meta?.role}
            {...meta.avatar}

            initialText={''}
            width={size.width}
            height={size.height}

            style={style}
            onSpeakEnd={onSpeakEnd}
            // other props that Puppet expects
        />
    );
});

export default Agent;
