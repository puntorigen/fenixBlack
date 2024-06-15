import React, { forwardRef, useRef, useEffect, useImperativeHandle } from 'react';
import Agent from './Agent'; // TODO rename Agent to Expert later
import { tools, avatar } from './constants';

const ResearchAnalyst = forwardRef(({
    id="analyst",
    name="Felipe",  // used for the displayed personality of the agent and maybe memory
    age=37,  // used for the displayed personality of the agent
    gender="male", // used for the displayed personality of the agent
    task="", // specific task for this agent instance
    style,
    onAnimationEnd,
}, ref) => {
    const expertRef = useRef(); 

    const meta = {
        type: 'expert',
        name,
        age,
        role: 'Research Analyst',
        goal: `Analyze the company website and provided description to extract insights on culture, values, and specific needs.`,
        backstory: `# Expert in analyzing company cultures and identifying key values and needs 
        from various sources, including websites and brief descriptions.
        # You cannot send emails to the client nor call them to ask for more information, so based all your responses on what you can find online and from your peers.`,
        // how the experts talks back to the user like in the meeting
        personality: `Always use 'I' instead of 'You', use easy to understand terms, don't use exagerated words, and be straightfoward on the tasks you are going to perform. Instead of saying you will perform in the future, say you are doing it now.`, 
        collaborate: true,
        avatar: {
            // dark blue color hex: #
            bgColor: '#1F286A',
            // darker brown color hex: #5C4033
            hairColor: '#331800', 
            shirtColor: '#606080', //#1F286A
            skinColor: avatar.skinColor.pale,
            glassesStyle: avatar.glassesStyle.square,
            facialHairStyle: avatar.facialHairStyle.scruff,
            hairStyle: avatar.hairStyle.turban,
            earSize: avatar.earSize.medium
        },
        tools: { // defines animations and which tools are available for this agent
            [tools.search]: { 'searching':'Searching websites for more information.' },
            [tools.scrape]: { 'reading': 'Reading the contents ..' },
            [tools.website_search]: { 'webpage': 'Reading the contents ..' },
            [tools.pdf_reader]: { 'reading': 'Reading PDF contents ..' },
            [tools.youtube_video_search]: { 'reading': 'Analyzing youtube video ..' },
        } 
    };
    if (task !== "") {
        meta.backstory += `. Your current main task is to '${task}'`;
    }

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
        getIDx: ()=>id
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
            bgColor={meta.avatar.bgColor}
            hairColor={meta.avatar.hairColor}
            shirtColor={meta.avatar.shirtColor}
            skinColor={meta.avatar.skinColor}
            style={style}
            onSpeakEnd={onAnimationEnd}
            // other props that Agent expects
        />
    );
});

export default ResearchAnalyst;
