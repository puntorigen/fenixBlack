import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle, Suspense } from 'react';
import NiceAvatar from '@nice-avatar-svg/react';
import lottie from 'lottie-web';
import { replaceColor, flatten } from 'lottie-colorify';
import { useSpeech } from "react-text-to-speech";

const Puppet = forwardRef(({
    bgColor="#6BD9E9", 
    hairColor="#000", 
    shirtColor="#FF0000", 
    skinColor="#F9C9B6", 
    earSize="small",
    hairStyle="fonze",
    noseStyle="curve",
    shirtStyle="collared",
    facialHairStyle="beard",
    glassesStyle="round",
    eyebrowsStyle="up",
    speakSpeed="400",
    blinkSpeed="1800",
    initialText="", 
    width = "300px",  // default width
    height = "300px",  // default height
    label = "",
    onSpeakEnd,
    style = {}
}, ref) => {
    const [text, setText] = useState(initialText);
    const [eyesStyle, setEyesStyle] = useState('circle');
    const [mouthStyle, setMouthStyle] = useState('smile');
    const [orientation, setOrientation] = useState({ flipped: false, look: 'center' }); 
    const [currentBgColor, setCurrentBgColor] = useState(bgColor);
    const [avatarBgColor, setAvatarBgColor] = useState("none"); //default transparent
    const [avatarStyle, setAvatarStyle] = useState({ scale: 1 });
    const [transitionStyle, setTransitionStyle] = useState({});
    
    const animationContainer = useRef(null);
    const animationInstance = useRef(null);
    const speakIntervalRef = useRef(null);
    const lastSizeRef = useRef(1);

    const SpeechCommands = useSpeech({ text, pitch: 1, rate: 1, volume: 1, lang: "en-US", voiceURI: "Aaron", highlightText: true });
    
    // Calculate scale and apply horizontal flip if needed
    const scale = Math.min(parseFloat(width) / 380, parseFloat(height) / 380);
    const transformStyle = `scale(${scale * avatarStyle.scale})${orientation.flipped ? ' scaleX(-1)' : ''}`;
    //const transformStyle = `scale(${scale})${orientation.flipped ? ' scaleX(-1)' : ''}`;
    const transformOrigin = `${orientation.flipped ? '56% 0%' : 'top left'}`;

    useEffect(() => {
        const blinkInterval = setInterval(() => {
            setEyesStyle(prev => (prev === 'circle' ? 'smiling' : 'circle'));
        }, Math.random() * blinkSpeed + 400);
    
        return () => clearInterval(blinkInterval);
    }, []);

    const clearSpeakInterval = () => {
        if (speakIntervalRef.current) {
            clearInterval(speakIntervalRef.current);
            setText(" ");
            speakIntervalRef.current = null;
        }
        try {
            if (SpeechCommands.speechStatus === "started") SpeechCommands.stop();
        } catch (error) {}
    };

    const speak = async(inputText, speed = speakSpeed, pause = 150, delayErase = 300, onEnd) => {
        clearSpeakInterval(); // Clear any existing interval to prevent overlap
        if (typeof inputText !== 'string' && Array.isArray(inputText)) {
            // for every item in inputText, call speak recursively waiting for the previous to finish
            const [first, ...rest] = inputText;
            await speak(first, speed, pause, delayErase, async() => {
                if (rest.length > 0) {
                    await speak(rest, speed, pause, delayErase, onEnd);
                }
            });
        } else {        
            const words = inputText.split(" ");
            let index = 0;
            if (SpeechCommands.speechStatus === "started") SpeechCommands.stop();
            if (SpeechCommands.speechStatus === "stopped" || SpeechCommands.speechStatus === "paused") SpeechCommands.start();
            speakIntervalRef.current = setInterval(async() => {
                if (index < words.length) {
                    setText(words.slice(0, index + 1).join(" "));
                    setMouthStyle(prev => (prev === 'smile' ? 'laughing' : 'smile'));
                    index++;
                } else {
                    clearSpeakInterval();
                    setTimeout(async() => {
                        setMouthStyle('smile');
                        setTimeout(async() => {
                            setText("");
                            console.log('puppet->speak->calling onEnd')
                            onEnd && await onEnd();  // Call the callback function if provided
                            onSpeakEnd && onSpeakEnd();  // Call the callback prop if provided
                        }, delayErase);
                    }, pause);
                }
            }, speed);
        }
    };

    const play = async(animationName, colors={}, loop=false) => {
        clearSpeakInterval(); // Clear any existing interval to prevent overlap
        if (animationInstance.current) {
            animationInstance.current.destroy();  // Destroy existing animation if any
        }
        const animationPath = `/animations/${animationName}.json`;
        if (colors && colors.bgcolor) {
            setCurrentBgColor(colors.bgcolor);
        } else {
            setCurrentBgColor(bgColor);
        }
        if (colors && colors.tint) { 
            const response = await fetch(animationPath);
            let data = await response.json();
            animationInstance.current = lottie.loadAnimation({
                container: animationContainer.current,
                renderer: 'svg',
                loop: loop,
                autoplay: true,
                animationData: flatten(colors.tint, data),
                rendererSettings: {
                    preserveAspectRatio: 'xMidYMid meet'
                }
            });
        } else {
            animationInstance.current = lottie.loadAnimation({
                container: animationContainer.current,
                renderer: 'svg',
                loop: loop,
                autoplay: true,
                path: animationPath,
                rendererSettings: {
                    preserveAspectRatio: 'xMidYMid meet'
                }
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

        // apply transition? only if downsizing
        const applyTransition = newSize < lastSizeRef.current;
        lastSizeRef.current = newSize;
        setTransitionStyle({
            transition: applyTransition ? 'transform 0.5s ease-out' : 'none'
        });

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
        stop: () => {
            clearSpeakInterval();
            if (animationInstance.current) {
                animationInstance.current.destroy();  // Destroy existing animation if any
            }
        },
        avatarSize,
        lookLeft: () => setOrientation({ ...orientation, flipped: true }),
        lookRight: () => setOrientation({ ...orientation, flipped: false }),
        lookUp: () => setOrientation({ ...orientation, look: 'up' }),   // Additional implementation needed for visual effect
        lookDown: () => setOrientation({ ...orientation, look: 'down' })  // Additional implementation needed for visual effect
    }));

    return (
        <div style={{ position: 'relative', width, height, display: 'inline-block', fontSize: 0, overflow: 'visible', ...style }}>
            { label && (<div className="nameTag">{label}</div>) }
            <div ref={animationContainer} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0, backgroundColor: currentBgColor }} />
            <div style={{ transform: transformStyle, transformOrigin: transformOrigin, position: 'relative', zIndex: 0, ...transitionStyle }}>
                <Suspense fallback={"Loading ..."}><NiceAvatar
                    shape="square"
                    bgColor={avatarBgColor}
                    shirtColor={shirtColor}
                    skinColor={skinColor}
                    earSize={earSize}
                    hairStyle={hairStyle}
                    hairColor={hairColor}
                    noseStyle={noseStyle}
                    glassesStyle={glassesStyle}
                    eyesStyle={eyesStyle}
                    facialHairStyle={facialHairStyle}
                    mouthStyle={mouthStyle}
                    shirtStyle={shirtStyle}
                    earRing="none"
                    eyebrowsStyle={eyebrowsStyle}
                /></Suspense>
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
                    maxHeight: height,
                    overflow: 'hidden',
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

export default Puppet;
