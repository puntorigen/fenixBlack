import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import NiceAvatar from '@nice-avatar-svg/react';
import lottie from 'lottie-web';
import { replaceColor, flatten } from 'lottie-colorify';

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
    const [avatarBgColor, setAvatarBgColor] = useState("none"); //default transparent
    const [avatarStyle, setAvatarStyle] = useState({ scale: 1, position: 'center' });
    
    const animationContainer = useRef(null);
    const animationInstance = useRef(null);
    const speakIntervalRef = useRef(null);

    // Calculate scale and apply horizontal flip if needed
    const scale = Math.min(parseFloat(width) / 380, parseFloat(height) / 380);
    const transformStyle = `scale(${scale * avatarStyle.scale})${orientation.flipped ? ' scaleX(-1)' : ''}`;
    //const transformStyle = `scale(${scale})${orientation.flipped ? ' scaleX(-1)' : ''}`;
    const transformOrigin = `${orientation.flipped ? '56% 0%' : 'top left'}`;

    useEffect(() => {
        const blinkInterval = setInterval(() => {
            setEyesStyle(prev => (prev === 'circle' ? 'smiling' : 'circle'));
        }, Math.random() * 1800 + 400);
    
        return () => clearInterval(blinkInterval);
    }, []);

    const clearSpeakInterval = () => {
        if (speakIntervalRef.current) {
            clearInterval(speakIntervalRef.current);
            speakIntervalRef.current = null;
        }
    };

    const speak = (inputText, speed = 400, pause = 150) => {
        clearSpeakInterval(); // Clear any existing interval to prevent overlap
        const words = inputText.split(" ");
        let index = 0;
        speakIntervalRef.current = setInterval(() => {
            if (index < words.length) {
                setText(words.slice(0, index + 1).join(" "));
                setMouthStyle(prev => (prev === 'smile' ? 'laughing' : 'smile'));
                index++;
            } else {
                clearSpeakInterval();
                setTimeout(() => {
                    setMouthStyle('smile');
                    setText("");
                    onSpeakEnd && onSpeakEnd();  // Call the callback function if provided
                }, pause);
            }
        }, speed);
    };

    const play = async(animationName, flattenColor, loop=false) => {
        if (animationInstance.current) {
            animationInstance.current.destroy();  // Destroy existing animation if any
        }
        const animationPath = `/animations/${animationName}.json`;
        setCurrentBgColor(bgColor);
        if (flattenColor) { 
            const response = await fetch(animationPath);
            let data = await response.json();
            animationInstance.current = lottie.loadAnimation({
                container: animationContainer.current,
                renderer: 'svg',
                loop: loop,
                autoplay: true,
                animationData: flatten(flattenColor, data)
            });
        } else {
            animationInstance.current = lottie.loadAnimation({
                container: animationContainer.current,
                renderer: 'svg',
                loop: loop,
                autoplay: true,
                path: animationPath
            });
        }
        animationInstance.current.addEventListener('enterFrame', () => {
            //console.log('debug anim',animationInstance.current);
            if (animationInstance.current.currentFrame >= animationInstance.current.totalFrames - 1) {
                if (!loop) {
                    console.log('animation ended');
                    setCurrentBgColor(bgColor);  // Reset background color once animation is complete
                    animationInstance.current.destroy();
                }
            }
        });
    };
  
    const avatarSize = (percentage='100%', customBgColor = '#333333') => {
        const newSize = parseFloat(percentage) / 100;
        setAvatarStyle({ scale: newSize });

        // Change the background color if the size is not 100%
        if (percentage === '100%') {
            setAvatarBgColor("none");  // Restore original background color
        } else {
            setAvatarBgColor(customBgColor);  // Set to dark grey
        }
    };

    useImperativeHandle(ref, () => ({
        speak,
        play,
        avatarSize,
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
                    bgColor={avatarBgColor}
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
