# actions.py - Place this file in the actions folder of your Rasa project

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker # type: ignore
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import pandas as pd
import os
import tempfile
import sys
import json

# Import your existing analysis functions
try:
    from .test_failure_analyzer import analyze_failures
except ImportError:
    # Fall back to direct import
    try:
        from test_failure_analyzer import analyze_failures
    except ImportError:
        # Create a placeholder if the module is not available
        def analyze_failures(df):
            return {
                "total_tests": len(df),
                "failure_count": len(df),
                "error_groups": [],
                "owner_stats": []
            }

# Import CDCARM URL actions
try:
    from .cdcarm_actions import (
        ActionGenerateCDCARMUrl,
        ActionGetCDCARMUrlWithReport,
        ActionGetCDCARMUrlWithoutReport,
        ActionOpenCDCARMUrl
    )
except ImportError:
    # Define these classes here if the import fails
    class ActionGenerateCDCARMUrl(Action):
        def name(self) -> Text:
            return "action_generate_cdcarm_url"
    
        def construct_cdcarm_url(self, investigation_status, cdcarm_owner=None, 
                                platform_id="1", release_id="217"):
            """
            Constructs a CDCARM URL with the given parameters
            
            Args:
                investigation_status (str): "NULL" or "NOT%20NULL" to filter by investigation report
                cdcarm_owner (str, optional): Owner name to filter by
                platform_id (str, optional): Platform ID
                release_id (str, optional): Release ID
                
            Returns:
                str: Fully constructed CDCARM URL
            """
            base_url = "https://cdcarm.win.ansys.com/Reports/Unified/ErrorReport/Product/90"
            
            # Basic parameters
            application_id = "-1"
            all_packages = "True"
            highlighter_collection = "MatchType%3DAll"
            official_only = "False"
            chronic_failure_threshold = "0"
            no_cache = "False"
            show_non_chronic_failures = "true"
            
            # Create filter collection
            filter_collection = f"MatchType%3DAll%26Filter0%3DType%3AARM.WebFilters.TestResults.Filters.InvestigationStatusFilter%2COperator%3AEQUAL%2CValue%3A{investigation_status}"
            
            # Add owner filter if provided
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
            platform_id = tracker.get_slot("platform_id") or "1"  # Default to 1
            release_id = tracker.get_slot("release_id") or "217"  # Default to 217
            
            # Check if we have entity overrides in the message
            owner_override = next(tracker.get_latest_entity_values("cdcarm_owner"), None)
            if owner_override:
                cdcarm_owner = owner_override
            
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
                                            platform_id, release_id)
            
            # Create a response message
            report_status = "with" if with_report else "without"
            owner_text = f" for owner {cdcarm_owner}" if cdcarm_owner else ""
            
            message = f"Here's your CDCARM URL {report_status} investigation report{owner_text}:\n\n{url}"
            
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
            
            # Get any owner entity from the message
            owner_override = next(tracker.get_latest_entity_values("cdcarm_owner"), None)
            if owner_override:
                cdcarm_owner = owner_override
                
            # Create a new URL generator
            url_generator = ActionGenerateCDCARMUrl()
            
            # Generate URL with investigation report
            url = url_generator.construct_cdcarm_url("NOT%20NULL", cdcarm_owner)
            
            # Create response message
            owner_text = f" for owner {cdcarm_owner}" if cdcarm_owner else ""
            message = f"Here's your CDCARM URL with investigation report{owner_text}:\n\n{url}"
            
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
            
            # Get any owner entity from the message
            owner_override = next(tracker.get_latest_entity_values("cdcarm_owner"), None)
            if owner_override:
                cdcarm_owner = owner_override
                
            # Create a new URL generator
            url_generator = ActionGenerateCDCARMUrl()
            
            # Generate URL without investigation report
            url = url_generator.construct_cdcarm_url("NULL", cdcarm_owner)
            
            # Create response message
            owner_text = f" for owner {cdcarm_owner}" if cdcarm_owner else ""
            message = f"Here's your CDCARM URL without investigation report{owner_text}:\n\n{url}"
            
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


# Your existing action classes
class ActionAnalyzeTestFailures(Action):
    def name(self) -> Text:
        return "action_analyze_test_failures"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the file path from a slot
        file_path = tracker.get_slot("uploaded_file_path")
        
        if not file_path or not os.path.exists(file_path):
            dispatcher.utter_message(text="I couldn't find the uploaded file. Please upload a CSV or Excel file with test failure data.")
            return []
        
        try:
            # Determine file type and read accordingly
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            else:
                # Assume CSV format
                df = pd.read_csv(file_path, delimiter='\t')
            
            # Run analysis
            analysis_results = analyze_failures(df)
            
            # Format the response
            response = self.format_analysis_for_chat(analysis_results)
            dispatcher.utter_message(text=response)
            
            # Store the analysis results for future reference
            return [SlotSet("analysis_results", analysis_results)]
            
        except Exception as e:
            dispatcher.utter_message(text=f"Error analyzing the file: {str(e)}")
            return []
    
    def format_analysis_for_chat(self, analysis_results):
        """Format the analysis results for the chat interface"""
        total_tests = analysis_results["total_tests"]
        failed_tests = analysis_results["failure_count"]
        failure_rate = round(failed_tests/total_tests*100 if total_tests > 0 else 0)
        
        response = f"📊 **Test Failure Analysis Summary**\n\n"
        response += f"Total Tests: {total_tests}\n"
        response += f"Failed Tests: {failed_tests} ({failure_rate}%)\n\n"
        
        response += "**Top Failure Patterns:**\n"
        for i, group in enumerate(analysis_results["error_groups"][:3]):
            response += f"{i+1}. **{group['pattern']}**: {group['count']} tests ({group['percentage']}%)\n"
        
        response += "\n**Most Affected Owners:**\n"
        for i, owner in enumerate(analysis_results["owner_stats"][:3]):
            response += f"{i+1}. **{owner['owner']}**: {owner['count']} tests ({owner['percentage']}%)\n"
        
        response += "\nYou can ask me for more details about specific patterns or owners, like:\n"
        if analysis_results["error_groups"]:
            pattern_example = analysis_results["error_groups"][0]["pattern"]
            response += f"- Tell me more about '{pattern_example}'\n"
        
        if analysis_results["owner_stats"]:
            owner_example = analysis_results["owner_stats"][0]["owner"]
            response += f"- Show me all failing tests for {owner_example}\n"
        
        return response

class ActionAnalyzeFailure(Action):
    """Action to analyze a specific test failure"""
    
    def name(self) -> Text:
        return "action_analyze_failure"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the test ID from an entity
        test_id = next(tracker.get_latest_entity_values("test_id"), None)
        
        if not test_id:
            dispatcher.utter_message(text="I couldn't identify which test you're asking about. Please provide a test ID like T-1234.")
            return []
        
        # Get the analysis results from the slot
        analysis_results = tracker.get_slot("analysis_results")
        
        if not analysis_results:
            dispatcher.utter_message(text=f"I don't have any analysis data yet. Please upload a test results file first.")
            return []
        
        # Look for the test in the analysis results
        found_test = None
        found_pattern = None
        
        for group in analysis_results["error_groups"]:
            for test in group["tests"]:
                if test["Test"] == test_id:
                    found_test = test
                    found_pattern = group["pattern"]
                    break
            if found_test:
                break
        
        if found_test:
            response = f"**Analysis for Test {test_id}**\n\n"
            response += f"This test is failing due to: **{found_pattern}**\n\n"
            response += f"Owner: {found_test['Owner']}\n\n"
            response += f"Error message:\n{found_test['ErrorMessage']}\n\n"
            
            # Find similar tests
            similar_tests = []
            for test in analysis_results["error_groups"]:
                if test["pattern"] == found_pattern:
                    for t in test["tests"]:
                        if t["Test"] != test_id:
                            similar_tests.append(t["Test"])
                    break
            
            if similar_tests:
                response += f"**Similar tests with the same issue:**\n"
                for i, test in enumerate(similar_tests[:5]):
                    response += f"{i+1}. {test}\n"
                
                if len(similar_tests) > 5:
                    response += f"... and {len(similar_tests) - 5} more\n"
            
            dispatcher.utter_message(text=response)
        else:
            dispatcher.utter_message(text=f"I couldn't find test {test_id} in the analysis results.")
        
        return []

class ActionExplainPrediction(Action):
    """Action to explain the prediction methodology"""
    
    def name(self) -> Text:
        return "action_explain_prediction"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        explanation = """
Our test failure prediction system works by analyzing patterns in historical test failures and correlating them with code changes.

**How it works:**

1. **Historical Data Analysis**: We analyze past test failures to identify patterns and common failure modes.

2. **Code Change Analysis**: We examine the current code changes to identify what areas of the codebase are being modified.

3. **Correlation**: We correlate these code changes with the historical failure patterns.

4. **Risk Assessment**: We calculate the likelihood of each test failing based on:
   - Similarity to past failure scenarios
   - Areas of code affected by current changes
   - Test coverage metrics
   - Developer history with similar changes

The system continually improves as it learns from new test results, making its predictions more accurate over time.

Would you like to know more about a specific aspect of the prediction system?
"""
        
        dispatcher.utter_message(text=explanation)
        return []