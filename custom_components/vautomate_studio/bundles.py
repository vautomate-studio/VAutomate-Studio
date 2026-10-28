"""Bundled suggestions are inert data, never installed or enabled during setup."""
BUNDLES = (
    {"id":"morning_curtains","version":1,"name":"Morning light","description":"Open your selected curtains at a time you choose.","default_time":"08:00","slots":[{"id":"curtains","label":"Curtains to open","domain":"cover","action":"open_cover","required":True}]},
    {"id":"evening_comfort","version":1,"name":"Evening comfort","description":"Turn on selected lights and optionally close the curtains.","default_time":"19:00","slots":[{"id":"lights","label":"Lights to turn on","domain":"light","action":"turn_on","required":True},{"id":"curtains","label":"Curtains to close · optional","domain":"cover","action":"close_cover","required":False}]},
    {"id":"goodnight","version":1,"name":"Goodnight","description":"Turn off selected lights and optionally pause your media.","default_time":"23:00","slots":[{"id":"lights","label":"Lights to turn off","domain":"light","action":"turn_off","required":True},{"id":"media","label":"Media to pause · optional","domain":"media_player","action":"media_pause","required":False}]},
    {"id":"evening_breeze","version":1,"name":"Evening breeze","description":"Start your selected fans at a time you choose.","default_time":"20:00","slots":[{"id":"fans","label":"Fans to start","domain":"fan","action":"turn_on","required":True}]},
)
