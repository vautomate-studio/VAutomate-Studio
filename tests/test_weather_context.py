"""Weather receives only permitted public day/night context, never coordinates."""
import unittest
import test_engine as f

class WeatherContextTest(unittest.TestCase):
    def setUp(self):
        fixture=f.EngineTest();fixture.setUp();self.adapter=fixture.adapter;self.document=fixture.document
        self.adapter.states['weather.home']={'entity_id':'weather.home','state':'sunny','attributes':{'temperature':27,'temperature_unit':'°C','password':'PRIVATE'},'last_updated':'2026-11-01T18:00:00+00:00'}
        self.adapter.states['sun.sun']={'entity_id':'sun.sun','state':'below_horizon','attributes':{'latitude':1,'longitude':2}}
        self.document['layout']['rooms'][0]['entities'].append('weather.home')
        self.engine=f.StudioEngine(self.adapter,self.document)
    def weather(self,actor):return next(s for s in self.engine.snapshot(actor) if s['entity_id']=='weather.home')
    def test_sun_context_is_public_boolean_not_location_or_raw_sun_entity(self):
        actor=f.Actor('admin','Owner',True,lambda _:True,lambda _:True)
        result=self.weather(actor);self.assertIs(result['attributes']['is_daytime'],False)
        self.assertNotIn('latitude',result['attributes']);self.assertNotIn('password',result['attributes'])
        self.assertEqual(result['last_updated'],'2026-11-01T18:00:00+00:00')
    def test_sun_context_respects_entity_read_permission(self):
        actor=f.Actor('member','Member',False,lambda entity:entity!='sun.sun',lambda _:False)
        self.assertNotIn('is_daytime',self.weather(actor)['attributes'])
    def test_home_sun_overrides_stale_provider_daylight(self):
        self.adapter.states['weather.home']['attributes']['is_daytime']=True
        actor=f.Actor('admin','Owner',True,lambda _:True,lambda _:True)
        self.assertIs(self.weather(actor)['attributes']['is_daytime'],False)

    def test_home_location_fallback_when_no_sun_entity(self):
        self.adapter.states.pop('sun.sun')
        self.adapter.weather_daylight=lambda:False
        actor=f.Actor('admin','Owner',True,lambda _:True,lambda _:True)
        self.assertIs(self.weather(actor)['attributes']['is_daytime'],False)
