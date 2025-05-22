from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

class ActionGenerateCDCARMUrl(Action):
    def name(self) -> Text:
        return "action_generate_cdcarm_url"

    def construct_cdcarm_url(self, investigation_status, cdcarm_owner=None, 
                            platform_id=None, release_id=None, application_id=None):
        """
        Constructs a CDCARM URL with the given parameters
        
        Args:
            investigation_status (str): "NULL" or "NOT%20NULL" to filter by investigation report
            cdcarm_owner (str, optional): Owner name to filter by (case sensitive)
            platform_id (str, optional): Platform ID (e.g., "1" for Windows)
            release_id (str, optional): Release ID (e.g., "217" for version 25.2)
            application_id (str, optional): Application ID (default "-1" for All Applications)
            
        Returns:
            str: Fully constructed CDCARM URL
        """
        # Set default values if not provided
        base_url = "https://cdcarm.win.ansys.com/Reports/Unified/ErrorReport/Product/90"
        platform_id = platform_id or "1"  # Default to Windows (1)
        release_id = release_id or "217"  # Default to release 25.2
        application_id = application_id or "-1"  # Default to All Applications
        
        # Basic parameters
        all_packages = "True"
        highlighter_collection = "MatchType%3DAll"
        official_only = "False"
        chronic_failure_threshold = "0"
        no_cache = "False"
        show_non_chronic_failures = "true"
        
        # Create filter collection - using the format from the screenshots
        # Use HAS_INVESTIGATION or NO_INVESTIGATION values based on screenshots
        if investigation_status == "NOT%20NULL":
            inv_status_value = "HAS_INVESTIGATION"
        else:
            inv_status_value = "NO_INVESTIGATION"
            
        filter_collection = f"MatchType%3DAll%26Filter0%3DType%3AARM.WebFilters.TestResults.Filters.InvestigationStatusFilter%2COperator%3AEQUAL%2CValue%3A{inv_status_value}"
        
        # Add owner filter if provided (case sensitive as noted)
        if cdcarm_owner:
            filter_collection += f"%26Filter1%3DType%3AARM.WebFilters.TestResults.Filters.OwnerFilter%2COperator%3AEQUAL%2CValue%3A{cdcarm_owner}"
    
        # Construct the URL
        url = (
            f"{base_url}?applicationId={application_id}&platformId={platform_id}&releaseId={release_id}&"
            f"allPackages={all_packages}&filterCollection={filter_collection}&highlighterCollection={highlighter_collection}&"
            f"officialOnly={official_only}&chronicFailureThreshold={chronic_failure_threshold}&noCache={no_cache}&"
            f"showNonChronicFailures={show_non_chronic_failures}"
        )
        
        return url

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Extract slots
        with_report = tracker.get_slot("with_investigation_report")
        cdcarm_owner = tracker.get_slot("cdcarm_owner")
        platform_id = tracker.get_slot("platform_id")
        release_id = tracker.get_slot("release_id")
        application_id = tracker.get_slot("application_id")
        
        # Check if we have entity overrides in the message
        owner_override = next(tracker.get_latest_entity_values("cdcarm_owner"), None)
        if owner_override:
            cdcarm_owner = owner_override
        
        # Check for platform override
        platform_override = next(tracker.get_latest_entity_values("platform"), None)
        if platform_override:
            # Map platform names to IDs if needed
            platform_map = {"windows": "1", "linux": "2", "mac": "3"}  # Example mapping
            platform_id = platform_map.get(platform_override.lower(), platform_override)
        
        # Check for release override
        release_override = next(tracker.get_latest_entity_values("release"), None)
        if release_override:
            # Map release names to IDs if needed
            release_map = {"25.2": "217"}  # Add more mappings as needed
            release_id = release_map.get(release_override, release_override)
        
        # Determine with/without report based on entity or intent
        report_entity = next(tracker.get_latest_entity_values("report_type"), None)
        if report_entity:
            with_report = report_entity.lower() != "without"
        
        # If slot is still None, default to with report
        if with_report is None:
            with_report = True
        
        # Set the investigation status based on whether we want a report or not
        investigation_status = "NOT%20NULL" if with_report else "NULL"
        
        # Generate the URL
        url = self.construct_cdcarm_url(investigation_status, cdcarm_owner, 
                                       platform_id, release_id, application_id)
        
        # Create a response message
        report_status = "with" if with_report else "without"
        owner_text = f" for owner {cdcarm_owner}" if cdcarm_owner else ""
        platform_text = f" on platform {platform_override}" if platform_override else ""
        release_text = f" for release {release_override}" if release_override else ""
        
        message = f"Here's your CDCARM URL {report_status} investigation report{owner_text}{platform_text}{release_text}:\n\n{url}"
        
        # Send the response
        dispatcher.utter_message(text=message)
        
        # Store the URL in a slot for future reference
        return [SlotSet("generated_url", url)]

class ActionGetCDCARMUrlWithReport(Action):
    """Shortcut action to get CDCARM URL with investigation report"""
    
    def name(self) -> Text:
        return "action_get_cdcarm_url_with_report"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the owner slot
        cdcarm_owner = tracker.get_slot("cdcarm_owner")
        platform_id = tracker.get_slot("platform_id")
        release_id = tracker.get_slot("release_id")
        
        # Get any owner entity from the message
        owner_override = next(tracker.get_latest_entity_values("cdcarm_owner"), None)
        if owner_override:
            cdcarm_owner = owner_override
        
        # Check for platform override
        platform_override = next(tracker.get_latest_entity_values("platform"), None)
        if platform_override:
            platform_map = {"windows": "1", "linux": "2", "mac": "3"}  # Example mapping
            platform_id = platform_map.get(platform_override.lower(), platform_override)
        
        # Check for release override
        release_override = next(tracker.get_latest_entity_values("release"), None)
        if release_override:
            release_map = {"25.2": "217"}  # Add more mappings as needed
            release_id = release_map.get(release_override, release_override)
            
        # Create a new URL generator
        url_generator = ActionGenerateCDCARMUrl()
        
        # Generate URL with investigation report - using HAS_INVESTIGATION value
        url = url_generator.construct_cdcarm_url("NOT%20NULL", cdcarm_owner, platform_id, release_id)
        
        # Create response message
        owner_text = f" for owner {cdcarm_owner}" if cdcarm_owner else ""
        platform_text = f" on platform {platform_override}" if platform_override else ""
        release_text = f" for release {release_override}" if release_override else ""
        
        message = f"Here's your CDCARM URL with investigation report{owner_text}{platform_text}{release_text}:\n\n{url}"
        
        # Send response
        dispatcher.utter_message(text=message)
        
        # Store the URL in a slot
        return [SlotSet("generated_url", url)]

class ActionGetCDCARMUrlWithoutReport(Action):
    """Shortcut action to get CDCARM URL without investigation report"""
    
    def name(self) -> Text:
        return "action_get_cdcarm_url_without_report"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the owner slot
        cdcarm_owner = tracker.get_slot("cdcarm_owner")
        platform_id = tracker.get_slot("platform_id")
        release_id = tracker.get_slot("release_id")
        
        # Get any owner entity from the message
        owner_override = next(tracker.get_latest_entity_values("cdcarm_owner"), None)
        if owner_override:
            cdcarm_owner = owner_override
        
        # Check for platform override
        platform_override = next(tracker.get_latest_entity_values("platform"), None)
        if platform_override:
            platform_map = {"windows": "1", "linux": "2", "mac": "3"}  # Example mapping
            platform_id = platform_map.get(platform_override.lower(), platform_override)
        
        # Check for release override
        release_override = next(tracker.get_latest_entity_values("release"), None)
        if release_override:
            release_map = {"25.2": "217"}  # Add more mappings as needed
            release_id = release_map.get(release_override, release_override)
            
        # Create a new URL generator
        url_generator = ActionGenerateCDCARMUrl()
        
        # Generate URL without investigation report - using NO_INVESTIGATION value
        url = url_generator.construct_cdcarm_url("NULL", cdcarm_owner, platform_id, release_id)
        
        # Create response message
        owner_text = f" for owner {cdcarm_owner}" if cdcarm_owner else ""
        platform_text = f" on platform {platform_override}" if platform_override else ""
        release_text = f" for release {release_override}" if release_override else ""
        
        message = f"Here's your CDCARM URL without investigation report{owner_text}{platform_text}{release_text}:\n\n{url}"
        
        # Send response
        dispatcher.utter_message(text=message)
        
        # Store the URL in a slot
        return [SlotSet("generated_url", url)]

class ActionOpenCDCARMUrl(Action):
    """Action to instruct the user how to open the generated URL"""
    
    def name(self) -> Text:
        return "action_open_cdcarm_url"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the generated URL
        url = tracker.get_slot("generated_url")
        
        if not url:
            dispatcher.utter_message(text="I don't have a generated URL yet. Please ask me to generate a CDCARM URL first.")
            return []
        
        # Provide instructions
        message = "To open the CDCARM URL, you can:\n\n"
        message += "1. Click on the URL above (if it's clickable)\n"
        message += "2. Copy the URL and paste it into your browser\n"
        message += "3. Use the 'Open URL' button in the interface if available\n\n"
        message += "Would you like me to generate a different URL?"
        
        dispatcher.utter_message(text=message)
        return []