# test_cdcarm_function.py

def construct_cdcarm_url(investigation_status, cdcarm_owner=None, 
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

# Test the function with various parameters
def test_url_generation():
    # Test 1: With investigation report (NOT NULL), no owner
    url1 = construct_cdcarm_url("NOT%20NULL")
    print("=== URL with investigation report, no owner ===")
    print(url1)
    print()
    
    # Test 2: Without investigation report (NULL), no owner
    url2 = construct_cdcarm_url("NULL")
    print("=== URL without investigation report, no owner ===")
    print(url2)
    print()
    
    # Test 3: With investigation report, with owner
    url3 = construct_cdcarm_url("NOT%20NULL", "JohnDoe")
    print("=== URL with investigation report, owner JohnDoe ===")
    print(url3)
    print()

if __name__ == "__main__":
    test_url_generation()