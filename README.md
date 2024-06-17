# Fenix Black
AI based multi-agent Marketing Agency

## Introduction
This web application simulates a virtual meeting environment where AI-driven avatars, each representing specialized experts, collaborate to complete designated tasks. The system uses a ReactJS frontend and Python FastAPI backend, with communication facilitated through Websockets.

## Features
- **Dynamic Avatars**: Utilizes [@nice-avatar-svg/react](https://www.npmjs.com/package/@nice-avatar-svg/react) for real-time avatar updates.
- **Interactive Meetings**: Avatars interact in a sequence within a virtual meeting space inspired by Google Meet.
- **Configurable Expert Components**: Users can define each expert's role, goals, backstory, and available tools.
- **Real-time Feedback**: Dynamically reflects the actions of experts during meetings, providing a comprehensive interactive experience.

## System Architecture
```mermaid
graph TD;
    Client[ReactJS Frontend] -->|Websockets| Server[Python FastAPI Backend];
    Server -->|JSON Messages| Client;
    Client -->|SVG Updates| Avatars[Dynamic SVG Avatars];
    Client -->|User Inputs| Server;
    Server -->|Processing Tasks| Server;
    Server -->|Update Status| Client;
```

<i>... readme in progress ...</i>
<br/> 
<br/> 
<img src="diagram.svg"/>
