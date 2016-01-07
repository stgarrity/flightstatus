Open-sourcing this after a few hours of hacking on Christmas Day … it’s far from done, and far from good, but it’s a start, and if I wait until it’s “done” I’ll never release it. If you’re not embarrassed you waited too long, or something like that.

Noticeably, the FlightAware API doesn’t actually support delays (so I’m planning on migrating the app to FlightStats, which seems to). I’d also like to integrate support with my calendar and/or TripIt (or please, please someone build a better TripIt! The functionality is so useful and the app is getting so much worse). Pull requests welcome ;)

Beware of hacks:

- AWS Lambda doesn’t support pytz yet, and I didn’t want to bother uploading it, so I hacked in two timezone classes for UTC and US/Pacific. This is super lame. I’ll fix it someday. Like that bug @adepue and @jtillman discovered yesterday that I supposedly introduced >5 years ago.

- I mostly fly United, and occasionally a few others, so this currently only supports a few airlines. Feel free to add as many as you want to the slots and the lame if-based translation code (it’ll at least be a dict lookup soon).

Releasing this under the GPLv3 license.

—

Start by pasting lambda.py into a new AWS Lambda function here:

https://console.aws.amazon.com/lambda/home?region=us-east-1

(NB: make sure to use us-east-1 because it’s the only one that Alexa can use according to the docs)

Then create an Amazon Echo app / Alexa Skills Kit here:

https://developer.amazon.com/edw/home.html#/skills/list

Take the Application Id from the app and paste it into the code where it says FIXME-APPLICATION-ID

Once you’ve saved the code, grab the ARN from the top right and put it in “Endpoint” under the app.

I use “flight status” as the invocation name (“Alexa, ask [flight status] for [United 123]”)

Get a FlightAware API key and put it into the code where it says FIXME-FLIGHTAWARE-USERNAME and FIXME-FLIGHTAWARE-SECRET