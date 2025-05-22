# actions.py - Updated with proper action registration

# Import Standard Libraries
import logging
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# Import CDCARM URL actions
try:
    from .cdcarm_url_actions import (
        ActionGenerateCDCARMUrl,
        ActionGetCDCARMUrlWithReport,
        ActionGetCDCARMUrlWithoutReport,
        ActionOpenCDCARMUrl
    )
except ImportError:
    logging.warning("Could not import CDCARM URL actions. Make sure cdcarm_url_actions.py is in the actions folder.")
    
    # Create dummy classes in case import fails
    class ActionGenerateCDCARMUrl(Action):
        def name(self) -> Text:
            return "action_generate_cdcarm_url"
        def run(self, dispatcher, tracker, domain):
            dispatcher.utter_message(text="Error: CDCARM URL actions module not loaded.")
            return []
            
    class ActionGetCDCARMUrlWithReport(Action):
        def name(self) -> Text:
            return "action_get_cdcarm_url_with_report"
        def run(self, dispatcher, tracker, domain):
            dispatcher.utter_message(text="Error: CDCARM URL actions module not loaded.")
            return []
            
    class ActionGetCDCARMUrlWithoutReport(Action):
        def name(self) -> Text:
            return "action_get_cdcarm_url_without_report"
        def run(self, dispatcher, tracker, domain):
            dispatcher.utter_message(text="Error: CDCARM URL actions module not loaded.")
            return []
            
    class ActionOpenCDCARMUrl(Action):
        def name(self) -> Text:
            return "action_open_cdcarm_url"
        def run(self, dispatcher, tracker, domain):
            dispatcher.utter_message(text="Error: CDCARM URL actions module not loaded.")
            return []

# Import CDCARM JSON fetch action
try:
    from .cdcarm_fetch_actions import ActionFetchCDCARMJson, ActionHandleCDCARMQuery
except ImportError:
    logging.warning("Could not import CDCARM fetch JSON action. Make sure cdcarm_fetch_actions.py is in the actions folder.")
    
    # Create dummy class in case import fails
    class ActionFetchCDCARMJson(Action):
        def name(self) -> Text:
            return "action_fetch_cdcarm_json"
        def run(self, dispatcher, tracker, domain):
            dispatcher.utter_message(text="Error: CDCARM JSON fetch action module not loaded.")
            return []
    
    class ActionHandleCDCARMQuery(Action):
        def name(self) -> Text:
            return "action_handle_cdcarm_query"
        def run(self, dispatcher, tracker, domain):
            dispatcher.utter_message(text="Error: CDCARM JSON fetch action module not loaded.")
            return []

# Keep your existing actions and imports...

# IMPORTANT: THIS LIST IS USED BY RASA TO REGISTER ACTIONS
# Make sure all your action classes are in this list
class ActionAnalyzeFailure(Action):
    def name(self) -> Text:
        return "action_analyze_failure"
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Analyzing failure...")
        return []

class ActionExplainPrediction(Action):
    def name(self) -> Text:
        return "action_explain_prediction"
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Explaining prediction...")
        return []

class ActionFetchTestData(Action):
    def name(self) -> Text:
        return "action_fetch_test_data"
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Fetching test data...")
        return []

class ActionAnalyzeTestFailures(Action):
    def name(self) -> Text:
        return "action_analyze_test_failures"
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Analyzing test failures...")
        return []