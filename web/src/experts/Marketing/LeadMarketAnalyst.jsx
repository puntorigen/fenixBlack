import React, { forwardRef, useRef, useEffect, useImperativeHandle } from 'react';
import Agent from '../Agent'; 
import { tools, avatar } from '../constants';

const LeadMarketAnalyst = forwardRef(({
    id="product_competitor",
    name="Christian",
    age=44,
    gender="male",
    style,
    onAnimationEnd,
    study=[],
}, ref) => {
    const expertRef = useRef();

    const meta = {
        type: 'expert',
        name,
        age,
        role: 'Lead Market Analyst',
        goal: `Conduct amazing analysis of the products and
				competitors, providing in-depth insights to guide
				marketing strategies.`,
        backstory: `# As the Lead Market Analyst at a premier
				digital marketing firm, you specialize in dissecting
				online business landscapes.
                # You cannot send emails to the client nor call them to ask for more information, so based all your responses on what you can find online and from your peers.`,
        collaborate: false,
        avatar: { 
            //dark-green color hex: 
            bgColor: '#29465B',
            hairColor: '#ff1010',
            shirtColor: '#C8F526',  
            skinColor: avatar.skinColor.pale,
            earSize: avatar.earSize.medium, 
            hairStyle: avatar.hairStyle.dannyPhantom,
            noseStyle: avatar.noseStyle.pointed, 
            shirtStyle: avatar.shirtStyle.open,
            facialHairStyle: avatar.facialHairStyle.none,
            glassesStyle: avatar.glassesStyle.none,
            eyebrowsStyle: avatar.eyebrowsStyle.down,
            speakSpeed: 500,
            blinkSpeed: 3000,
        },
        tools: { // defines animations and which tools are available for this agent
            [tools.search]: { 'searching':'Searching websites for more information.' },
            [tools.website_search]: { 'searching':'Searching website for more information.' },
            //[tools.scrape]: { 'analyzing:#FFFFFF': 'Understanding the design ..' },
            [tools.pdf_reader]: { 'reading': 'Reading pdf ..' },
            [tools.youtube_video_search]: { 'reading': 'Searching on youtube video transcription ..' },
        },
        study: study
    };

    const setup = () => {
        // Example: set up Agent based on AccountManager's props like age and gender
        if (expertRef.current) {
            expertRef.current.lookLeft();
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

export default LeadMarketAnalyst;
