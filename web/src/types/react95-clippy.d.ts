// src/types/react95-clippy.d.ts

declare module '@react95/clippy' {
    import React from 'react';
  
    interface ClippyProps {
      agentName?: string;
      children?: React.ReactNode;
    }
  
    export function ClippyProvider(props: ClippyProps): JSX.Element;
    export function useClippy(): { clippy: ClippyAgent };
  
    interface ClippyAgent {
      speak: (message: string) => void;
      play: (animation: string) => void;
      show: () => void;
    }
  }
  