import os
import logging
from flask import Flask
import certifi
import time
import re
import requests # *
import json
from slack import WebClient
from slackeventsapi import SlackEventAdapter
import ssl
from expense import ExpenseBot

#credentials for auth come from backend Slack account and app auth- exported in py venv
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET= os.environ.get('SLACK_SIGNING_SECRET')

#activate Slack credentials from Source, raise RuntimeError if absent
if SLACK_BOT_TOKEN is None or SLACK_SIGNING_SECRET is None:
    raise RuntimeError("Error: Unable to find environment keys. Exiting.")


#globals
app = Flask(__name__) #Flask app to run server
slack_events_adapter = SlackEventAdapter(os.environ["SLACK_SIGNING_SECRET"], "/slack/events", app) #slack adaptor to listen for events
bot_slack_client = WebClient(SLACK_BOT_TOKEN) #access bot capabilities


#Master dictionary that tracks expenses for that user through conversational flow, totalCost initialized to 0
userExpenses = {}
userExpenses['totalCost'] = 0

def start_onboarding(user_id: str, channel: str):
    """initiate onboarding message- Using bot class from expense
        for clean initial markdown display
    """
    # Create a new welcome message.
    Bot = ExpenseBot(channel)
    # Get the onboarding message payload
    message = Bot.get_welcomeMessage_payload()
    # Post the onboarding message in Slack
    response = bot_slack_client.chat_postMessage(**message)

def post_response(channel: str, response: str):
    """Helper method posts desired non-welcome message bot response in message".
    """
    message = {
            "ts": '',
            "channel": channel,
            "username": 'expenseBot',
            "icon_emoji": ':moneybag:',
            "text": response
        }
    bot_slack_client.chat_postMessage(**message)


def add_method(channel: str, text: str):
    ''' Method to handle adding single expense item
    '''

    #input sanitzation
    if len(text.split()) != 2:
        response = "Please put your expense in format: add [Expense]:[DollarValue]"
    #add expense as key and amount as value into expense Dictionary
    else:
        expense = text.split()[1]
        item = expense.split(':')[0]
        cost = int(expense.split(':')[1])
        userExpenses[item] = cost
        userExpenses['totalCost'] += cost
        response = "Excellent, we have added your expense of: " + item + " with a cost of $" + str(cost)

    post_response(channel,response)

def remove_method(channel: str, text: str):
    ''' Method to handle removing single expense item
    '''

    if len(userExpenses.keys()) == 1: #no expenses except totalCost, can't remove anything
        response = "You currently have no expenses, so nothing can be removed!"
        post_response(channel,response)
        return

    if len(text.split()) != 2:
        response = "Please put your expense in format: remove [Expense]"
    # check to see if item is valid expense and remove, or inform user valid options
    else:
        expense = text.split()[1]
        if expense not in userExpenses.keys():
            possibleExpenses = ''
            for index, expense in enumerate(userExpenses.keys()):
                if expense != 'totalCost': #add all expenses to string, for last item forgo comma
                    if index != len(userExpenses.keys())-1:
                        possibleExpenses += expense + ', '
                    else:
                        possibleExpenses += expense
            response = "Sorry, I do not see that item in your expenses. Your expenses include: " + possibleExpenses
        else:
            response = "Excellent, we have removed your expense of: " + expense + " with a cost of $" + str(userExpenses[expense])
            userExpenses['totalCost'] -= userExpenses[expense]
            del userExpenses[expense]


    post_response(channel,response)

def view_method(channel: str, text: str):
    ''' Method to view all itemized expenses
    '''
    #if no expenses return message, otherwise put all expenses and DollarValue into single string
    if len(userExpenses.keys()) == 1: #no expenses except totalCost, can't remove anything
        response = "You currently have no expenses, so nothing to view!"
    else:
        response = 'Your expenses and their respective costs are as follows: '
        for index, expense in enumerate(userExpenses.keys()):
            if expense != 'totalCost': #add all expenses and cost to string, for last item forgo comma
                if index != len(userExpenses.keys())-1:
                    response += expense + ':$' +str(userExpenses[expense]) + ', '
                else:
                    response += expense + ':$' + str(userExpenses[expense])


    post_response(channel, response)

def total_method(channel: str, text: str):
    ''' Method to return total amount owed for all expenses
    '''
    totalCost = userExpenses['totalCost']
    if totalCost==0:
        response = 'You are all settled up!'
    else:
        response = "The total amount you are owed is: $" + str(totalCost)

    post_response(channel, response)

def clear_method(channel: str, text: str):
    ''' Method to clear all expenses
    '''

    #clear all expenses iteratively from global variable to prevent scoping issues- create copy to prevent dictioinary size change
    expensesCopy = tuple(userExpenses.keys())
    for expense in expensesCopy:
        if expense != 'totalCost':
            del userExpenses[expense]

    userExpenses['totalCost'] = 0
    response = "We have cleared all your expenses, please confirm with card company to ensure payment."

    post_response(channel, response)

#listen for slack events using adaptor, and if a message is sent, filter response through this method
@slack_events_adapter.on("message")
def message(payload):
    """Handle user messaging and fork logic based on user option selection".
    """

    event = payload.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")


    #hard coded userID for Haroun to filter out Bot response and avoid infinite loop- fine for single user
    if user_id == 'U010PEBLK89':
        if text and text.lower() == "start": #initial message- display onboarding
            return start_onboarding(user_id, channel_id)
        elif text and "add" in text.lower(): #user wants to add expense
            return add_method(channel_id, text)
        elif text and "remove" in text.lower(): #user wants to remove expense
            return remove_method(channel_id, text)
        elif text and "view" in text.lower(): #user wants to view all expenses
            return view_method(channel_id, text)
        elif text and "total" in text.lower(): #user wants to total all expenses
            return total_method(channel_id, text)
        elif text and "clear" in text.lower(): #user wants to clear all expenses
            return clear_method(channel_id, text)
        #Catchall for unprocessable input
        else:
            response = "Sorry, we are unable to adequately parse your response at this time. Please use keywords from main menu."
            post_response(channel_id, response)

# Main loop- running flask server
if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    app.run(port=3000)
