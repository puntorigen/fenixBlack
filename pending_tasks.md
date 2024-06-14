tasks:
- create 'thinking' method animation state for 'Agent' component
- [x] assign mapping for tools ids and names within 'meeting' class
- add further actionActivity mapping on 'reportAgentSteps'
- add 'Agent' support for RAG
- [x] add support for multiple lines of text on 'Agent' speak exposed method
- [x] add support for 'Agent', speak onEnd callback, to chain several calls to a single Agent
- [in progress] add expert 'Agent' personality field for adapting responses as narrative
    - add API endpoint that accepts an Expert profile and a text, and returns
      the text as if said by the Expert with his personality applied, as if chatting on
      a meeting.
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