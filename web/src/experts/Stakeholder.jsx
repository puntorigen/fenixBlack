import React, { forwardRef, useRef, useEffect, useImperativeHandle } from 'react';
import Agent from './Agent'; // TODO rename Agent to Expert later
import { tools, avatar } from './constants';

const Stakeholder = forwardRef(({
    id="stakeholder",
    name="Julio",
    age=23,
    phone="+12345678901", // international format "+1 234 567 8901
    user_name="Pablo",
    user_role="CEO",
    user_company="",
    style,
    onAnimationEnd,
    study=[], 
}, ref) => {
    const expertRef = useRef();

    const meta = {
        type: 'expert',
        name,
        age,
        role: 'Stakeholder',
        goal: `Represent the user on the team and is able to call the user once per session to ask for missing information.`,
        backstory: `# Act as a professional PR expert, that excels at representing the requesting task user within the team.
        # You have all the past knowledge of previous conversations with the user, and you use that source as the first reference.
        # But you can also make a single call to the user to ask for missing information. If you do so, collect all the needed questions from your peers in advance, because you only have one call per session.
        # You also need to be able to understand the user's needs and be able to communicate them to the team.`,
        collaborate: true,
        avatar: {  
            bgColor: '#29465B', //sky blue 
            hairColor: '#000000', 
            shirtColor: '#F52626',
            skinColor: avatar.skinColor.pale,
            earSize: avatar.earSize.medium, 
            hairStyle: avatar.hairStyle.fonze,
            noseStyle: avatar.noseStyle.pointed, 
            shirtStyle: avatar.shirtStyle.open,
            facialHairStyle: avatar.facialHairStyle.none,
            glassesStyle: avatar.glassesStyle.square,
            eyebrowsStyle: avatar.eyebrowsStyle.eyelashesUp,
            speakSpeed: 200,
            blinkSpeed: 3000,
        },
        tools: { // defines animations and which tools are available for this agent
            //[tools.search]: { 'searching':'Searching websites for more information.' },
            //[tools.website_search]: { 'searching':'Searching website for more information.' },
            //[tools.scrape]: { 'analyzing:#FFFFFF': 'Understanding the design ..' },
            //[tools.pdf_reader]: { 'pdf_reader': 'Reading pdf ..' }, 
            //[tools.youtube_video_search]: { 'reading': 'Searching on youtube video transcription ..' },
            //[tools.query_visual_website]: { 'camera': 'Querying webpage visually ..' },
            [tools.call]: { 
                meta: {
                    'max_duration': 300, // 5 minute (300 seconds default)
                    'intro_message': 'Hello, this is Julio, the Stakeholder for the team. I am calling you to ask for more information about the task we are working on.',
                    'target': phone, // the phone number to call (intl format)
                    'language': 'en-US', // the language to use for the call
                    'context': {
                        'user_name': user_name,
                        'user_role': user_role,
                        'user_company': user_company,
                    }
                },
                'phone':'Calling the user for more information.' 
            },
        }, 
        study: study,
        max_num_iterations: 3 
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

export default Stakeholder;
