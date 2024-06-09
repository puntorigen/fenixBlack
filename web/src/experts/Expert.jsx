import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import NiceAvatar from '@nice-avatar-svg/react';

const Expert = forwardRef(({
    bgColor="#6BD9E9", 
    hairColor="#000", 
    shirtColor="#00DD00", 
    skinColor="#F9C9B6", 
    initialText="", 
    width = "300px",  // default width
    height = "300px",  // default height
    onSpeakEnd
}, ref) => {
    const [text, setText] = useState(initialText);
    const [eyesStyle, setEyesStyle] = useState('circle');
    const [mouthStyle, setMouthStyle] = useState('smile');

    // Calculate scale based on the desired size and the default size of the avatar (380x380)
    const scale = Math.min(parseFloat(width) / 380, parseFloat(height) / 380);
  
    useEffect(() => {
        const blinkInterval = setInterval(() => {
            setEyesStyle(prev => (prev === 'circle' ? 'smiling' : 'circle'));
        }, Math.random() * 1800 + 400);
    
        return () => clearInterval(blinkInterval);
    }, []);

    const speak = (inputText, speed = 400, pause = 150) => {
        const words = inputText.split(" ");
        let index = 0;
        let speakInterval = setInterval(() => {
            if (index < words.length) {
                setText(words.slice(0, index + 1).join(" "));
                setMouthStyle(prev => (prev === 'smile' ? 'laughing' : 'smile'));
                index++;
            } else {
                clearInterval(speakInterval);
                setTimeout(() => {
                    setMouthStyle('smile');
                    onSpeakEnd && onSpeakEnd();  // Call the callback function if provided
                }, pause);
            }
        }, speed);
    };
  
    useImperativeHandle(ref, () => ({
        speak
    }));

    return (
        <div style={{ position: 'relative', width, height, display: 'inline-block', fontSize: 0, overflow: 'visible' }}>
            <div style={{ transform: `scale(${scale})`, transformOrigin: 'top left', position: 'relative', zIndex: 0 }}>
                <NiceAvatar
                    shape="square"
                    bgColor={bgColor}
                    shirtColor={shirtColor}
                    skinColor={skinColor}
                    earSize="small"
                    hairStyle="fonze"
                    hairColor={hairColor}
                    noseStyle="curve"
                    glassesStyle="round"
                    eyesStyle={eyesStyle}
                    facialHairStyle="beard"
                    mouthStyle={mouthStyle}
                    shirtStyle="collared"
                    earRing="none"
                    eyebrowsStyle="up"
                />
            </div>
            {text && (
                <div style={{
                    position: 'absolute',
                    bottom: '0',
                    left: '0',
                    right: '0',
                    textAlign: 'center',
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    color: 'white',
                    padding: '5px 0px 10px 0px',
                    maxWidth: width,
                    fontSize: `${scale * 20}px`,  // Dynamically adjust font size based on scale
                    zIndex: 1
                }}>
                    {text}
                </div>
            )}
        </div>
    );
});

export default Expert;
