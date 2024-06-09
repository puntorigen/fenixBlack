import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import NiceAvatar from '@nice-avatar-svg/react';
import lottie from 'lottie-web';

const Expert = forwardRef(({
    bgColor="#6BD9E9", 
    hairColor="#000", 
    shirtColor="#FF0000", 
    skinColor="#F9C9B6", 
    initialText="", 
    width = "300px",  // default width
    height = "300px",  // default height
    onSpeakEnd,
    style = {}
}, ref) => {
    const [text, setText] = useState(initialText);
    const [eyesStyle, setEyesStyle] = useState('circle');
    const [mouthStyle, setMouthStyle] = useState('smile');
    const [orientation, setOrientation] = useState({ flipped: false, look: 'center' }); 
    const [currentBgColor, setCurrentBgColor] = useState(bgColor);
    const animationContainer = useRef(null);
    const animationInstance = useRef(null);

    // Calculate scale and apply horizontal flip if needed
    const scale = Math.min(parseFloat(width) / 380, parseFloat(height) / 380);
    const transformStyle = `scale(${scale})${orientation.flipped ? ' scaleX(-1)' : ''}`;
    const transformOrigin = `${orientation.flipped ? '56% 0%' : 'top left'}`;

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

    const play = (animationName) => {
        if (animationInstance.current) {
            animationInstance.current.destroy();  // Destroy existing animation if any
        }
        const animationPath = `/animations/${animationName}.json`;
        setCurrentBgColor('none');  // Make avatar background translucent
        animationInstance.current = lottie.loadAnimation({
            container: animationContainer.current,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: animationPath
        });
        animationInstance.current.addEventListener('complete', () => {
            setCurrentBgColor(bgColor);  // Reset background color once animation is complete
        });
    };
  
    useImperativeHandle(ref, () => ({
        speak,
        play,
        lookLeft: () => setOrientation({ ...orientation, flipped: true }),
        lookRight: () => setOrientation({ ...orientation, flipped: false }),
        lookUp: () => setOrientation({ ...orientation, look: 'up' }),   // Additional implementation needed for visual effect
        lookDown: () => setOrientation({ ...orientation, look: 'down' })  // Additional implementation needed for visual effect
    }));

    return (
        <div style={{ position: 'relative', width, height, display: 'inline-block', fontSize: 0, overflow: 'visible', ...style }}>
            <div ref={animationContainer} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0, backgroundColor: currentBgColor }} />
            <div style={{ transform: transformStyle, transformOrigin: transformOrigin, position: 'relative', zIndex: 0 }}>
                <NiceAvatar
                    shape="square"
                    bgColor={currentBgColor}
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
