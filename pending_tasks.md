tasks:
- [x] assign mapping for tools ids and names within 'meeting' class
- [x] add further actionActivity mapping on 'reportAgentSteps'
- add 'Agent' support for RAG ('study' prop)
- [x] add support for multiple lines of text on 'Agent' speak exposed method
- [x] add support for 'Agent', speak onEnd callback, to chain several calls to a single Agent
- [x] add expert 'Agent' personality field for adapting responses as narrative
    - add API endpoint that accepts an Expert profile and a text, and returns
      the text as if said by the Expert with his personality applied, as if chatting on
      a meeting.
- [x] unify meeting related things on meeting class
- [] add support for additional realtime/running meeting context
    - a ws command for adding context to a meeting by some avatar_id (expert or user)
    - a tool for experts to query the 'live context' if available using RAG
    - this would allow us to add live feedback from the user
    - add 'Meeting' method for adding context to 'ws room', like .addMeetingContent('who',what)
        - would connect to the ws backend, and send the command /add_context to the room
        - the server would receive the command an add the given object to the running context 

- [ ] add running meeting timer on Meeting component (with prop showTime=true)
- [ ] add more tools:
    - [x] switched 'scape' for 'rag' internally
    - [x] add visual website query using vision LLM
    - [] add token tracker per tool, using envs or db per meeting session

- add meeting summary support on finishMeeting
- add meeting layout support
- add whiteboard component support
- [ ] add meeting duration tracker
- [ ] add Meeting hide and show methods; hidden by default
- [ ] add on expert show up animation
- [ ] add Service component (parent director of meetings)
    - [ ] add basic input tools (InputField, InputPDF, etc)
    - [ ] add support for 'study' input elements output for specific expert (ex. InputPDF name='guidelines', as Designer expert prop item study 'guidelines'; by not being an url, it'll search the named outputs and use them as inputs)
- [ ] impplement Meeting 'rules' on experts adaptTextStyle and meeting output
- [ ] add support for input in any language and output on same, even if internal thinking is always english
- [ ] add 'reflectAndLearn' support for every 'named' expert, at the end of each meeting, asks the LLM what did the expert learned from the experience and saves it to a special 'expert' RAG, it can query as a tool in the future. This gets triggered when the Meeting component (or Service) has the prop 'learn=true'.
- [ ] add special 'HiExpert' (intro message for other team members) call to create a stylized hello message for each expert, considering their role, name, output language, backstory and past experiences.
- [ ] prepend to every 'expert' backstory the local date and time, so they know which results are newest. 
- (future) add user avatar (humanInput) integration on meeting (experts/User)


step:
    action.tool
    action.observation -> result of tool