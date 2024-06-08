// src/avatars/AvatarBase.tsx
import 'jquery';
import React from 'react';
import clippy from 'clippyjs';
import './clippyStyles.css'; // Ensure your CSS is correctly imported

export abstract class AvatarBase extends React.Component<{ clippyAgent: string }, {}> {
    name: string | null = null;
    role: string | null = null;
    goal: string | null = null;
    backstory: string | null = null;
    private agentInstance: any | null = null;  // No longer static
    isIdle: boolean = true;

    constructor(props: { clippyAgent: string }) {
        super(props);
        this.initializeAttributes();
    }

    abstract initializeAttributes(): void;

    loadAgent = () => {
        clippy.load(this.props.clippyAgent, (agent: any) => {
            this.agentInstance = agent; // Each instance gets its own agent
            this.onLoad();
            // Setup an interval or a similar method to monitor the queue length
            const queueMonitor = setInterval(() => {
                if (this.agentInstance && this.agentInstance._queue._queue.length === 0) {
                    if (!this.isIdle) {
                        console.log(`${this.name} agent is now idle.`);
                        this.isIdle = true;
                    }
                    //clearInterval(queueMonitor);  // Clear the interval when not needed
                } else {
                    if (this.isIdle) {
                        console.log('this.agentInstance._queue._queue',this.agentInstance._queue._queue);
                        console.log(`${this.name} agent is now busy.`);
                        this.isIdle = false;
                    }
                }
            }, 100);  // Check every 100ms
        }, () => {
            console.error('Failed to load Clippy agent:', this.props.clippyAgent);
        }, '/agents/');
        //https://cdn.jsdelivr.net/gh/pi0/clippyjs@master/assets/agents/
    }

    onLoad = () => {}

    show = () => {
        this.agentInstance?.show();
    }

    hide = () => {
        this.agentInstance?.stop();
        this.agentInstance?.hide();
    }

    idle = () => {
        this.agentInstance?.animate();
    }

    stop = () => {
        this.agentInstance?.stop();
    }

    wait = (ms: number) => {
        this.agentInstance?.delay(ms);
    }

    moveTo = (x: number, y: number) => {
        this.agentInstance?.stopCurrent();
        this.agentInstance?.moveTo(x, y);
        this.agentInstance?.animate();
    }

    lookTo = (x: number, y: number) => {
        this.agentInstance?.gestureAt(x, y);
    }

    hello = () => {
        this.agentInstance?.show();
        this.speak(`Hello, I am ${this.name}, the ${this.role}.`);
        this.agentInstance?.play('Greet');
    }

    speak = (text: string) => {
        this.agentInstance.speak(text);
    }

    say = (text: string) => this.speak(text);

    AgentComponent = () => {
        React.useEffect(() => {
            this.loadAgent();
            return () => {
                //this.agentInstance?.stop();
                //this.agentInstance?.hide();
            }
        }, []);

        return null;  // This component does not render anything itself
    }
}
