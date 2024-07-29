from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json() # Payload is the diagnostic info in dialog flow

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    # yeh waali info is there in 'Diagnostic info' in dialog flow
    intent = payload['queryResult']['intent']['displayName']    # this line means --> you have intent, displayName under queryResult
    parameters = payload[s'queryResult']['parameters']   # parameters under queryResult
    output_contexts = payload['queryResult']['outputContexts']  # outputContexts under queryResult

    if intent == "Track.Order- context: Ongoing-Tracking":
        return JSONResponse(content={
            "fulfillmentText": f"Received =={intent}== in the backend"
        })