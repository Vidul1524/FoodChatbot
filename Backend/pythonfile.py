# Required Modules
from fastapi import FastAPI
from fastapi import Request # to handle incoming HTTP requests.
from fastapi.responses import JSONResponse # to send JSON responses
import database_helper
import Generic_helper

app = FastAPI()  #initializes the FastAPI application

# Session id: coz there might be multiple chatbots and multiple users might be working !!!
# This dictionary stores orders that are currently being processed.
inprogress_orders = {}

# inprogress_orders = {
#     'session_id_1': {'pizza': 2, 'gamosa': 1},
#     'session_id_2': {'chole': 5, 'vada pav': 3, 'mango lassi': 1}
# }


# Handling POST Requests
@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json() # Payload is the diagnostic info in dialog flow


    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    # yeh waali info is there in 'Diagnostic info' in dialog flow
    intent = payload['queryResult']['intent']['displayName']    # this line means --> you have intent, displayName under queryResult
    parameters = payload['queryResult']['parameters']   # parameters under queryResult
    output_contexts = payload['queryResult']['outputContexts']  # outputContexts under queryResult
    session_id = Generic_helper.extract_session_id(output_contexts[0]["name"])

    # Maps intents to their respective handler functions.
    # This mean for eg: if intent is 'Order.Add - context: Ongoing-Order' then it will be replaced by add_to_order function
    intent_handler_dict = {
        'Order.Add - context: Ongoing-Order': add_to_order,
        'Order.Remove - context: Ongoing-Order': remove_from_order,
        'Order.Complete - context: Ongoing-Order': complete_order,
        'Track.Order- context: Ongoing-Tracking': track_order
    }

    return intent_handler_dict[intent](parameters, session_id)


# Saves the order to the database
def save_to_db(order: dict):
    # fore eg: order={"pizza":2,"samosa":1}
    next_order_id = database_helper.get_next_order_id()  # Retrieves the next order ID

    # Insert individual items along with quantity in orders table
    for food_item, quantity in order.items():
        # Inserts each item in the order.
        rcode = database_helper.insert_order_item( food_item, quantity, next_order_id )  #inserting

        if rcode == -1:
            return -1

    # Now insert order tracking status
    database_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id



# Completes the order---->
def complete_order(parameters: dict, session_id: str):
    # Checks if the session ID is in progress.
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)  # Saves the order to the database --- !!
        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                               "Please place a new order again"
        else:
            # Retrieves the total order price.
            order_total = database_helper.get_total_order_price(order_id)

            fulfillment_text = f"Awesome. We have placed your order. " \
                               f"Here is your order id # {order_id}. " \
                               f"Your order total is {order_total} which you can pay at the time of delivery!"

        del inprogress_orders[session_id]   # delete the current inprogress order so that we can take another order
    # Returns a JSON response with the fulfillment text.
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# Adds items to an order---
# Working:
# I need 2 pizza and 1 samosa  -->call add_to_order function  ---> dict: {"pizza":2, "samosa":1}
# Again after asking do you need anything else?
# add one mango lassi ---> dict: {"pizza":2, "samosa":1, "mango lassi":1}
def add_to_order(parameters: dict, session_id: str):

    food_items = parameters["Food-Items"]
    quantities = parameters["number"]

    # Checks if the number of food items and quantities match.
    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry I didn't understand. Can you please specify food items and quantities clearly?"
    # Updates the in-progress order or creates a new one.
    else:
        # takes 2 or more datasets and 'zips' them together
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id] = current_food_dict
        else:
            inprogress_orders[session_id] = new_food_dict

        order_str = Generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# Removes items from an order---
def remove_from_order(parameters: dict, session_id: str):
    # step1: locate the session id record
    # step2: get the value from dictionary: {"vada pav": 3, "mango lassi":1}
    # step3: remove the food items. eg: request: ["vada pav"]
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
        })
    # Removes specified items from the order.
    food_items = parameters["Food-Items"]
    current_order = inprogress_orders[session_id]

    removed_items = []
    no_such_items = []

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulfillment_text = f' Your current order does not have {",".join(no_such_items)}'

    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = Generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# Tracks the status of an order---So fi
def track_order(parameters: dict, session_id: str):
    order_id = int(parameters['order_id'])
    order_status = database_helper.get_order_status(order_id) #taking status from database_halper.py
    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# Run using this in terminal below
# uvicorn pythonfile:app --reload