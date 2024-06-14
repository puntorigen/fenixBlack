import React, { forwardRef, useRef, useEffect, useImperativeHandle } from 'react';
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
        meta: () => meta,
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
                    puppetRef.current.avatarSize('20%','#29465B');
                    puppetRef.current.speak(text,400,150,textDelay,()=>{
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
            bgColor={meta.avatar.bgColor}
            hairColor={meta.avatar.hairColor}
            shirtColor={meta.avatar.shirtColor}
            skinColor={meta.avatar.skinColor}
            
            earSize={meta.avatar.earSize} 
            hairStyle={meta.avatar.hairStyle}
            noseStyle={meta.avatar.noseStyle}
            shirtStyle={meta.avatar.shirtStyle}
            facialHairStyle={meta.avatar.facialHairStyle}
            glassesStyle={meta.avatar.glassesStyle}
            speakSpeed={meta.avatar.speakSpeed}
            blinkSpeed={meta.avatar.blinkSpeed}
            eyebrowsStyle={meta.avatar.eyebrowsStyle}

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
