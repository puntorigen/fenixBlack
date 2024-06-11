import React, { forwardRef, useRef, useImperativeHandle } from 'react';
import Puppet from './Puppet';

const Agent = forwardRef(({
    name,
    age,
    gender,
    style,
    onAnimationEnd,
}, ref) => {
    const puppetRef = useRef();

    // Map Agent props to Puppet props or methods
    const handleSetup = () => {
        // Example: set up Puppet based on Agent's props like age and gender
        if (puppetRef.current) {
            puppetRef.current.setAge(age);
            puppetRef.current.setGender(gender);
        }
    };

    // Expose Puppet's methods to Agent's parent through ref
    useImperativeHandle(ref, () => ({
        play: () => {
            if (puppetRef.current) {
                puppetRef.current.play('smile'); // example method
            }
        },
        customMethod: () => {
            handleSetup();
        },
        // Directly forwarding methods
        ...puppetRef.current
    }));

    return (
        <Puppet
            ref={puppetRef}
            name={name}
            style={style}
            onSpeakEnd={onAnimationEnd}
            // other props that Puppet expects
        />
    );
});

export default Agent;
