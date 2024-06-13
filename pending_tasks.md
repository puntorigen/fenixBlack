tasks:
- create 'thinking' method animation state for 'Agent' component
- assign mapping for tools ids and names within 'meeting' class
- add further actionActivity mapping on 'reportAgentSteps'
- add 'Agent' support for RAG
- add support for multiple lines of text on 'Agent' speak exposed method
- add support for 'Agent', speak onEnd callback, to chain several calls to a single Agent
- add expert 'Agent' personality field for adapting responses as narrative
    - add API endpoint that accepts an Expert profile and a text, and returns
      the text as if said by the Expert with his personality applied, as if chatting on
      a meeting.
- add running meeting timer on Meeting component (with prop showTime=true)
- add more tools:
    - scrapeVisual: webpage->pdf, understand PDF layout output

- add meeting summary support on finishMeeting
- add meeting layout support
- add whiteboard component support

- (future) add user avatar (humanInput) integration on meeting (experts/User)


step:
    action.tool
    action.observation -> result of tool