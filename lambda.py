"""
Leaving this here in case it's helpful for people reading this code...it's based on the sample kit

This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function

import urllib2
import json
import datetime


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if (event['session']['application']['applicationId'] !=
        “FIXME-APPLICATION-ID“):
        raise ValueError("Invalid Application ID")

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "FlightStatus":
        return flight_status(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    else:
        raise ValueError("Invalid intent")


# --------------- Functions that control the skill's behavior ------------------


def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Please say an airline and flight number"

    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please say an airline (United, Delta, Jet Blue, Alaska, American, and Virgin) and flight number"
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def flight_status(intent, session):

    if 'Airline' not in intent['slots'] or 'FlightNumber' not in intent['slots']:
        return get_welcome_response()

    # hacking these classes in right now because AWS Lambda doesn't support an easy "import pytz" and I didn't upload it yet
    class TZ_UTC(datetime.tzinfo):

        def utcoffset(self, dt):
            return datetime.timedelta(0)

        def dst(self, dt):
            return datetime.timedelta(0)

        def tzname(self, dt):
            return "UTC"

    class TZ_PST(datetime.tzinfo):

        def utcoffset(self, dt):
            return datetime.timedelta(hours=-8) + self.dst(dt)

        def dst(self, dt):
            # DST starts last Sunday in March
            d = datetime.datetime(dt.year, 4, 1)   # ends last Sunday in October
            self.dston = d - datetime.timedelta(days=d.weekday() + 1)
            d = datetime.datetime(dt.year, 11, 1)
            self.dstoff = d - datetime.timedelta(days=d.weekday() + 1)
            if self.dston <=  dt.replace(tzinfo=None) < self.dstoff:
                return datetime.timedelta(hours=1)
            else:
              return datetime.timedelta(0)

        def tzname(self, dt):
            return "US/Pacific"

    airline_name = intent['slots']['Airline']['value']
    airline_code = ""

    # these happen to be airlines I care about right now, need to convert to a dict lookup or better
    if airline_name == "united":
        airline_code = "UA"
    elif airline_name == "delta":
        airline_code = "DL"
    elif airline_name == "jet blue":
        airline_code = "JBU"
    elif airline_name == "alaska" or airline_name == "alaska airlines":
        airline_code = "ASA"
    elif airline_name == "american" or airline_name == "american airlines":
        airline_code = "AAL"
    elif airline_name == "virgin" or airline_name == "virgin america":
        airline_code = "VRD"

    ident = "%s%s" % (airline_code, intent['slots']['FlightNumber']['value'])

    req = urllib2.Request("http://flightxml.flightaware.com/json/FlightXML2/FlightInfo?ident=%s" % ident)
    req.add_header("Authorization", "Basic %s" % (“FIXME-FLIGHTAWARE-USERNAME:FIXME-FLIGHTAWARE-SECRET”.encode("base64")[:-1]))
    resp = urllib2.urlopen(req)

    data = json.loads(resp.read())

    flights = data['FlightInfoResult']['flights']

    for flight in flights:
        estimated_arrival_time = datetime.datetime.fromtimestamp(int(flight['estimatedarrivaltime']))
        if estimated_arrival_time.date() == datetime.date.today():
            break

    airline_name = intent['slots']['Airline']['value']
    flight_number = intent['slots']['FlightNumber']['value']

    speech_output = ""

    if flight['actualdeparturetime'] == 0:  # flight hasn't left yet
        filed_departure_time = datetime.datetime.fromtimestamp(int(flight['filed_departuretime']))
        delta = filed_departure_time - datetime.datetime.now()

        # FIXME this doesn't necessarily handle delays on departure? nor does it say on-time or late because FlightAware API sucks

        speech_output = "%s %s is departing %s for %s in %s hours and %s minutes" % (airline_name,
                                                                                     flight_number,
                                                                                     flight['originCity'],
                                                                                     flight['destinationCity'],
                                                                                     delta.seconds / (60*60),
                                                                                     (delta.seconds % (60*60)) / 60)

    elif flight['actualarrivaltime'] != 0:  # flight has already landed
        actual_arrival_time = datetime.datetime.fromtimestamp(int(flight['actualarrivaltime']))
        delta = datetime.datetime.now() - actual_arrival_time
        hours = delta.seconds / (60*60)

        speech_output = "%s %s arrived at %s %s%s%s minutes ago" % (airline_name,
                                                                            flight_number,
                                                                            flight['destinationCity'],
                                                                            hours if hours > 0 else "",
                                                                            " hours and " if (hours > 1) else (" hour and " if (hours == 1) else ""),
                                                                            (delta.seconds % (60*60)) / 60)

    elif estimated_arrival_time > datetime.datetime.now():  # flight is in the air
        estimated_arrival_time = estimated_arrival_time.replace(tzinfo=TZ_UTC())
        estimated_arrival_time = estimated_arrival_time.astimezone(tz=TZ_PST())

        speech_output = "%s %s is arriving at %s on time at %s" % (airline_name,
                                                                   flight_number,
                                                                   flight['destinationCity'],
                                                                   estimated_arrival_time.strftime("%H:%M")
                                                                   )
    else:
        speech_output = "Sorry, this flight doesn't match our parameters...check the logs"

    return build_response({}, build_speechlet_response(
        "Flight Status", speech_output, "", True))

# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }