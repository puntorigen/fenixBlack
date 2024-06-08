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
    state = {
        isIdle: true // Assume the avatar starts in an idle state
    };

    constructor(props: { clippyAgent: string }) {
        super(props);
        this.initializeAttributes();
    }

    abstract initializeAttributes(): void;

    loadAgent = () => {
        clippy.load(this.props.clippyAgent, (agent: any) => {
            this.agentInstance = agent; // Each instance gets its own agent
            //agent.show();
            this.onLoad();
        }, () => {
            console.error('Failed to load Clippy agent:', this.props.clippyAgent);
        }, '/agents/');
        //https://cdn.jsdelivr.net/gh/pi0/clippyjs@master/assets/agents/
    }

    onLoad = () => {}

    show = () => {
        this.agentInstance?.show();
        this.agentInstance?.play('Greet');
    }

    hide = () => {
        this.agentInstance?.stop();
        this.agentInstance?.hide();
    }

    moveTo = (x: number, y: number) => {
        this.agentInstance?.stop();
        this.agentInstance?.moveTo(x, y);
        this.agentInstance?.animate();
    }

    hello = () => {
        this.agentInstance?.show();
        //this.agentInstance?.play('Greet');
        this.say(`Hello, I am ${this.name}, the ${this.role}.`);
    }

    say = (message: string) => {
        this.agentInstance?.speak(message);
    }

    AgentComponent = () => {
        React.useEffect(() => {
            this.loadAgent();
            return () => {
                this.agentInstance?.stop();
                this.agentInstance?.hide();
            }
        }, []);

        return null;  // This component does not render anything itself
    }
}
