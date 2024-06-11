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

    const setup = () => {
        // Example: set up Puppet based on Agent's props like age and gender
        if (puppetRef.current) {
            puppetRef.current.setAge(age);
            puppetRef.current.setGender(gender);
        }
    };

    // Expose Puppet's methods to Agent's parent through ref
    useImperativeHandle(ref, () => ({
        // Inherit Puppet methods
        ...puppetRef.current,
        // Custom methods
        meta: () => {
            return {
                name,
                age,
            }
        },
        play: () => {
            if (puppetRef.current) {
                puppetRef.current.play('smile'); // example method
            }
        }
    }));

    useEffect(() => {
        setup(); // Set up Puppet when Agent is mounted
    }, []);

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
