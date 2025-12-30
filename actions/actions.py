from typing import Any, Text, Dict, List
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


class ExtractFoodEntity(Action):

    def name(self) -> Text:
        return "action_extract_food_entity"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        food_entity = tracker.get_slot('food')

        if food_entity:
            dispatcher.utter_message(text=f"You ordered {food_entity}")
        else:
            dispatcher.utter_message(text="I dont know what you want")
        return []

 

class ActionGetWeather(Action):
    def name(self) -> Text:
        return "action_get_weather"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        api_key = "API Key"
        
        # Get location from NLU entities
        location = None
        for entity in tracker.latest_message.get('entities', []):
            if entity['entity'] in ['city', 'GPE', 'location']:
                location = entity['value']
                break
        
        if not location:
            dispatcher.utter_message(
                text="Sorry, I can't recognize the location."
            )
            return []
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('cod') == 200:
                city = data['name']
                country = data['sys']['country']
                weather = data['weather'][0]['description'].title()
                temp = data['main']['temp']
                humidity = data['main']['humidity']
                wind = data['wind']['speed']
                
                response_text = (
                    f"🌤️ Weather in {city}, {country}:\n"
                    f"• Condition: {weather}\n"
                    f"• Temperature: {temp}°C\n"
                    f"• Humidity: {humidity}%\n"
                    f"• Wind: {wind} m/s"
                )
                
                dispatcher.utter_message(text=response_text)
                
            elif data.get('cod') == '404':
                dispatcher.utter_message(text=f"City '{location}' not found.")
            else:
                dispatcher.utter_message(text="Couldn't fetch weather data.")
                
        except Exception as e:
            dispatcher.utter_message(text="Weather service error.")
            print(f"Weather API error: {e}")
        
        return []


 

class ActionLocateHealthCenters(Action):
    def name(self) -> Text:
        return "action_health_centers_locating"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get location from NLU entities
        location = None
        for entity in tracker.latest_message.get('entities', []):
            if entity['entity'] in ['city', 'GPE', 'location']:
                location = entity['value']
                break
        
        if not location:
            dispatcher.utter_message(
                text="Sorry, I can't recognize the location."
            )
            return []
        
        dispatcher.utter_message(text=f"Searching near {location}...")
        
        try:
            # Get coordinates
            geolocator = Nominatim(user_agent="health_bot")
            geo = geolocator.geocode(location)
            
            if not geo:
                dispatcher.utter_message(text=f"Couldn't find {location}.")
                return []
            
            # Search for hospitals/clinics
            query = f"""
            [out:json][timeout:25];
            node["amenity"~"hospital|clinic"](around:10000,{geo.latitude},{geo.longitude});
            out;
            """
            
            url = "https://overpass-api.de/api/interpreter"
            response = requests.get(url, params={'data': query}, timeout=30)
            data = response.json()
            
            facilities = []
            for element in data.get('elements', []):
                name = element.get('tags', {}).get('name', 'Unknown')
                if name != 'Unknown':
                    # Calculate distance
                    dist = geodesic((geo.latitude, geo.longitude), 
                                   (element['lat'], element['lon'])).km
                    facilities.append({
                        'name': name,
                        'distance': round(dist, 2)
                    })
            
            if facilities:
                # Sort by distance and take top 5
                facilities.sort(key=lambda x: x['distance'])
                response_text = f"🏥 Health centers near {location}:\n\n"
                
                for i, fac in enumerate(facilities[:5], 1):
                    response_text += f"{i}. {fac['name']}\n"
                    response_text += f"   📏 {fac['distance']} km away\n\n"
                
                dispatcher.utter_message(text=response_text)
            else:
                dispatcher.utter_message(text=f"No health centers found near {location}.")
                
        except Exception as e:
            dispatcher.utter_message(text="Search service error.")
            print(f"Health center error: {e}")
        
        return []


class ExtractCityEntity(Action):

    def name(self) -> Text:
        return "action_extract_city_entity"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        city_value = tracker.get_slot("city")
        if not city_value:
            for entity in tracker.latest_message.get('entities', []):
                if entity.get('entity') in ['city', 'GPE', 'location']:
                    city_value = entity.get('value')
                    break

        if city_value:
            dispatcher.utter_message(text=f"Got it. I'll use {city_value}.")
            return [SlotSet("city", city_value)]
        else:
            dispatcher.utter_message(text="I couldn't identify a city. Tell me the location.")
            return []


class ActionCareerAdvice(Action):

    def name(self) -> Text:
        # Match domain action name (note the spelling)
        return "action_carrer_advice"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_text = tracker.latest_message.get('text', '')
        advice = "Consider your interests, strengths, and market demand. Try internships or projects to explore paths, and network with professionals."
        if any(k in (user_text or '').lower() for k in ["data", "ml", "ai"]):
            advice = "Data/ML is strong: build math/stats foundations, practice with real datasets, and showcase projects (Kaggle, GitHub)."
        elif any(k in (user_text or '').lower() for k in ["web", "frontend", "backend"]):
            advice = "Web dev: pick a stack (React/Node or Django), build 3–5 portfolio apps, and learn deployments."

        dispatcher.utter_message(text=advice)
        return []


class ActionMatchResults(Action):

    def name(self) -> Text:
        return "action_match_results"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        team = tracker.get_slot('team')
        if not team:
            for entity in tracker.latest_message.get('entities', []):
                if entity.get('entity') == 'team':
                    team = entity.get('value')
                    break

        if team:
            dispatcher.utter_message(text=f"I don't have live results, but I can track {team}. Check your sports app for latest scores.")
            return [SlotSet('team', team)]
        else:
            dispatcher.utter_message(text="Which team should I check results for?")
            return []
