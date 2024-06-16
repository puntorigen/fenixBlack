# tool idea
# call phone number, text to say, transcribe user speach and return 
1. create tool as a special fastapi endpoint that performs the tasks, because:
    - we need to expose a websocket url for grabbing the twilio streaming response
    - we need to expose a POST endpoint that returns the twilioML to be said 
    - we need to create an ngrok tunnel for twilio to get back to us with the data
    - we need to set a maximum amount of calls (maybe just 1 per crew execution)
    - we return the data on the specific starting endpoint to the tool 