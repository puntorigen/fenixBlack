import React, { forwardRef, useRef, useEffect, useImperativeHandle } from 'react';
import Puppet from './Puppet';

const Agent = forwardRef(({
    bgColor="#6BD9E9", 
    hairColor="#000", 
    shirtColor="#FF0000", 
    skinColor="#F9C9B6",
    width = "300px",  // default width
    height = "300px",  // default height
    style = {},
    meta = {},
    tools = {},
    onSpeakEnd,
}, ref) => {
    const puppetRef = useRef();

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
        meta: () => meta,
        play: async(tool='search',bgcolor='#6BD9E9',textDelay=2000) => {
            if (puppetRef.current) {
                if (tool in tools) {
                    let animKey = Object.keys(tools[tool])[0]; // searching
                    let text = tools[tool][animKey];
                    let extra = {};
                    if (animKey.indexOf(':') !== -1) {
                        extra = { tint: animKey.split(':')[1] };
                        animKey = animKey.split(':')[0];
                    }
                    await puppetRef.current.play(animKey,{ bgcolor, ...extra },true);
                    puppetRef.current.avatarSize('20%','#29465B');
                    puppetRef.current.speak(text,400,150,textDelay);
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
            bgColor={bgColor}
            hairColor={hairColor}
            shirtColor={shirtColor}
            skinColor={skinColor}
            initialText={''}
            width={width}
            height={height}

            style={style}
            onSpeakEnd={onSpeakEnd}
            // other props that Puppet expects
        />
    );
});

export default Agent;
