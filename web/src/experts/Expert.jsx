import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import NiceAvatar from '@nice-avatar-svg/react';

const Expert = forwardRef(({
    bgColor="#6BD9E9", 
    hairColor="#000", 
    shirtColor="#FF0000", 
    skinColor="#F9C9B6", 
    initialText="", 
    width = "300px",  // default width
    height = "300px",  // default height
    flipped = false,
    onSpeakEnd,
    style = {}
}, ref) => {
    const [text, setText] = useState(initialText);
    const [eyesStyle, setEyesStyle] = useState('circle');
    const [mouthStyle, setMouthStyle] = useState('smile');

    // Calculate scale and apply horizontal flip if needed
    const scale = Math.min(parseFloat(width) / 380, parseFloat(height) / 380);
    const transformStyle = `scale(${scale})${flipped ? ' scaleX(-1)' : ''}`;
    const transformOrigin = `${flipped ? '56% 0%' : 'top left'}`;

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
        <div style={{ position: 'relative', width, height, display: 'inline-block', fontSize: 0, overflow: 'visible', ...style }}>
            <div style={{ transform: transformStyle, transformOrigin: transformOrigin, position: 'relative', zIndex: 0 }}>
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
                    padding: '5px 5px 10px 5px',
                    maxWidth: width,
                    fontFamily: 'Arial, sans-serif',
                    fontSize: `${scale * 20}px`,  // Dynamically adjust font size based on scale
                    zIndex: 1,
                }}>
                    {text}
                </div>
            )}
        </div>
    );
});

export default Expert;
