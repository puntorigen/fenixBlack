import React, { forwardRef, useRef, useEffect, useImperativeHandle } from 'react';
import Agent from './Agent'; // TODO rename Agent to Expert later

const AccountManager = forwardRef(({
    name="Mauricio",
    age=37,
    gender="male",
    style,
    onAnimationEnd,
}, ref) => {
    const expertRef = useRef();

    const meta = {
        type: 'expert',
        name,
        age,
        role: 'Account Manager',
        goal: `Manage client accounts and ensure customer satisfaction.`,
        backstory: `Experienced in leading customer success teams within tech industries, adept at solving complex client issues.`,
        collaborate: true,
        avatar: {
            bgColor: '#6BD9E9',
            hairColor: '#000000',
            shirtColor: '#1F286A',
            skinColor: '#c68642',
        }
    };

    // Define how tools are animated within the AccountManager
    const tools = {
        search: { 'searching':'Searching websites for more information.' },
        scrape: { 'analyzing:#FFFFFF': 'Reading the contents ..' },
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
        other: ()=>{}
    }));

    useEffect(() => {
        setup(); // Set up Agent when specialist is mounted
    }, []);

    return (
        <Agent
            ref={expertRef}
            meta={meta}
            tools={tools}
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

export default AccountManager;
