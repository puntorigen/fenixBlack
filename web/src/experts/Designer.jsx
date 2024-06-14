import React, { forwardRef, useRef, useEffect, useImperativeHandle } from 'react';
import Agent from './Agent'; // TODO rename Agent to Expert later
import { tools, avatar } from './constants';

const Designer = forwardRef(({
    id="designer",
    name="Christian",
    age=44,
    gender="male",
    style,
    onAnimationEnd,
}, ref) => {
    const expertRef = useRef();

    const meta = {
        type: 'expert',
        name,
        age,
        role: 'Designer',
        goal: `Create visually appealing and user-friendly designs, and brand identify guidelines, brochures, etc.`,
        backstory: `With a decade of experience in graphic and digital design, specializing in UX/UI and brand identity, you search all the needed information to create the best design, paying special attention into crafting design related queries, and adapting the responses to use materials a developer can understand.`,
        collaborate: true,
        avatar: {
            bgColor: '#E75A01', 
            hairColor: '#fbe7a1',
            shirtColor: '#C8F526',  
            skinColor: avatar.skinColor.pale,
            earSize: avatar.earSize.medium, 
            hairStyle: avatar.hairStyle.dannyPhantom,
            noseStyle: avatar.noseStyle.pointed, 
            shirtStyle: avatar.shirtStyle.open,
            facialHairStyle: avatar.facialHairStyle.none,
            glassesStyle: avatar.glassesStyle.none,
            eyebrowsStyle: avatar.eyebrowsStyle.eyelashesUp,
            speakSpeed: 500,
            blinkSpeed: 3000,
        },
        tools: { // defines animations and which tools are available for this agent
            [tools.search]: { 'searching':'Searching websites for more information.' },
            [tools.website_search]: { 'searching':'Searching website for more information.' },
            [tools.scrape]: { 'analyzing:#FFFFFF': 'Understanding the design ..' },
            [tools.pdf_reader]: { 'reading': 'Reading pdf ..' },
            [tools.youtube_video_search]: { 'reading': 'Searching on youtube video transcription ..' },
        }
    };

    const setup = () => {
        // Example: set up Agent based on AccountManager's props like age and gender
        if (expertRef.current) {
            //expertRef.current.setAge(age);
            //expertRef.current.setGender(gender);
        }
    };

    // Expose Agent's methods to AccountManager's parent through ref
    useImperativeHandle(ref, () => ({
        // Inherit Agent methods
        ...expertRef.current,
        // Custom methods
        other: ()=>{}
    }));

    useEffect(() => {
        setup(); // Set up Agent when specialist is mounted
    }, []);

    return (
        <Agent
            ref={expertRef}
            id={id}
            meta={meta}
            name={name}            
            style={style}
            onSpeakEnd={onAnimationEnd}
            // other props that Agent expects
        />
    );
});

export default Designer;
