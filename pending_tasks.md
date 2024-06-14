tasks:
- create 'thinking' method animation state for 'Agent' component
- [x] assign mapping for tools ids and names within 'meeting' class
- add further actionActivity mapping on 'reportAgentSteps'
- add 'Agent' support for RAG ('study' prop)
- [x] add support for multiple lines of text on 'Agent' speak exposed method
- [x] add support for 'Agent', speak onEnd callback, to chain several calls to a single Agent
- [in progress] add expert 'Agent' personality field for adapting responses as narrative
    - add API endpoint that accepts an Expert profile and a text, and returns
      the text as if said by the Expert with his personality applied, as if chatting on
      a meeting.
- [] unify meeting related things on meeting class
- [] add support for additional realtime/running meeting context
    - a ws command for adding context to a meeting by some avatar_id (expert or user)
    - a tool for experts to query the 'live context' if available using RAG
    - this would allow us to add live feedback from the user
    - add 'Meeting' method for adding context to 'ws room', like .addMeetingContent('who',what)
        - would connect to the ws backend, and send the command /add_context to the room
        - the server would receive the command an add the given object to the running context 

- add running meeting timer on Meeting component (with prop showTime=true)
- add more tools:
    - [x] switched 'scape' for 'rag' internally

- add meeting summary support on finishMeeting
- add meeting layout support
- add whiteboard component support

- (future) add user avatar (humanInput) integration on meeting (experts/User)


step:
    action.tool
    action.observation -> result of tool