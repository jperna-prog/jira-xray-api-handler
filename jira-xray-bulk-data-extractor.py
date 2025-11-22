
# ==============================================================================
# SCRIPT NAME: JIRA_XRAY_BULK_DATA_EXTRACTOR.PY
# ==============================================================================
# 
# FUNCTIONAL DESCRIPTION:
# This script performs a highly robust, automated extraction of all accessible 
# Jira issues (including Test Management entities, Stories, and Bugs) from the 
# configured Jira Cloud instance. 
# 
# It uses the Keyset/ID Pagination strategy (ORDER BY id) to bypass common API 
# offset limitations and indexing issues, ensuring complete data retrieval 
# across all visible projects for comprehensive BI analysis.
# 
# AUTHOR: Juan Perna
# DATE: November 22, 2025
# 
# ==============================================================================


import requests
import json
# ... (The rest of your code follows here)
import requests
import json
import os
import time
import pandas as pd 
import openpyxl
from datetime import datetime

# --- 1. CONFIGURATION ---
# Script relies on these environment variables being set externally.
CLIENT_ID = os.getenv("XRAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("XRAY_CLIENT_SECRET")
PROXY_URL = os.getenv("PROXY_URL") 
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_BASE_URL = "https://bancoicbc.atlassian.net"


# --- VALIDATION ---
if not (JIRA_EMAIL and JIRA_API_TOKEN):
     print("ERROR: Missing Jira credentials.")
     exit(1)

# ======================================================================
#                STEP 1: PROJECT DISCOVERY
# ======================================================================

def get_all_accessible_projects() -> list:
    """
    Queries the Jira API for a list of ALL projects visible to the user.
    Returns a list of project keys (e.g., ['UPMU', 'SDI', 'MBD']).
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/project"
    print("INFO: Querying Jira project catalog...")
    
    try:
        with requests.Session() as session:
            session.auth = (JIRA_EMAIL, JIRA_API_TOKEN)
            session.headers.update({"Accept": "application/json"})
            
            response = session.get(url, timeout=20)
            response.raise_for_status()
            
            projects_data = response.json()
            
            # Extract only the project KEYS
            project_keys = [p['key'] for p in projects_data]
            
            print(f"SUCCESS: Found {len(project_keys)} accessible projects.")
            print(f"Examples: {', '.join(project_keys[:5])}...")
            
            return project_keys
            #return ['GDP'] # For testing a single project

    except Exception as e:
        print(f"CRITICAL ERROR while listing projects: {e}")
        return []

# ======================================================================
#                STEP 2: EXTRACTION PER PROJECT
# ======================================================================

def get_issues_from_project(project_key: str) -> list:
    """
    Downloads ALL content (Issues) from a single specified project using 
    Keyset/ID pagination. The function continues until the end of the project 
    is reached or a safety limit is hit.

    Args:
        project_key (str): The key of the project to query (e.g., 'UPMU').

    Returns:
        list: A list of raw issue dictionaries from the Jira API.
    """
    search_url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    project_issues = []
    max_results = 100 
    
    search_url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    project_issues = []
    max_results = 100 
    
    # JQL: Everything from this project (No issue type filtering, per request)
    base_jql = f'project = "{project_key}" and issuetype in(Test, "Test Execution", "Test plan", "Test set", "Precondition", "Bug")'  
    

    SAFETY_LIMIT = 50000 
    
    last_seen_id = None

    with requests.Session() as session:
        session.auth = (JIRA_EMAIL, JIRA_API_TOKEN)
        session.headers.update({"Accept": "application/json"})
        
        while True:
            if len(project_issues) >= SAFETY_LIMIT:
                print(f"   !!! Safety limit reached for {project_key}.")
                break

            # ID Pagination (Descending)
            if last_seen_id is None:
                current_jql = f'{base_jql} ORDER BY id DESC'
            else:
                current_jql = f'{base_jql} AND id < {last_seen_id} ORDER BY id DESC'

            params = {
                'jql': current_jql,
                'maxResults': max_results,
                # Requested fields (expanded for metrics and debugging)
                'fields': 'key,summary,status,created,updated,id,project,issuetype,reporter,assignee,priority,components,labels,resolution,fixVersions,issuelinks,timeoriginalestimate',
                'validateQuery': 'strict'
            }
            
            try:
                response = session.get(search_url, params=params, timeout=30)
                
                # If project access is denied (401, 403), skip to the next project
                if response.status_code in [401, 403]:
                    print(f"   ⚠️ Access denied to project {project_key}. Skipping...")
                    return []
                
                response.raise_for_status()
                data = response.json()
                issues = data.get('issues', [])
                
                if not issues:
                    break # End of project

                project_issues.extend(issues)
                last_seen_id = issues[-1]['id'] 
                
            except Exception as e:
                print(f"   ERROR in {project_key}: {e}")
                break
                        
    return project_issues

# ======================================================================
#                STEP 3: EXCEL REPORT GENERATION
# ======================================================================

def generate_excel_report(issues: list, filename: str = "consolidated_report.xlsx"):
    """
    Transforms a list of raw Jira issue dictionaries into a Pandas DataFrame,
    parses nested fields (like reporter, links, time tracking), and exports
    the resulting table to a standardized Excel file.
    
    Includes new columns for Creation Month and Year.

    Args:
        issues (list): List of issue dictionaries to process.
        filename (str): Name of the Excel file to generate.
    """
    if not issues: return
    print(f"\nINFO: Generating Master Excel Report with {len(issues)} records...")
    
    rows = []
    for issue in issues:
        key = issue.get('key', 'N/A')
        fields = issue.get('fields', {})
        
        # Safe extraction of nested objects
        project_info = fields.get('project', {})
        issuetype_info = fields.get('issuetype', {})
        reporter_info = fields.get('reporter') or {}
        assignee_info = fields.get('assignee') or {}
        priority_info = fields.get('priority') or {}
        resolution_info = fields.get('resolution') or {}
        
        # Lists (Joined by comma)
        components = ", ".join([c['name'] for c in fields.get('components', [])])
        fix_versions = ", ".join([v['name'] for v in fields.get('fixVersions', [])])
        labels = ", ".join(fields.get('labels', []))
        
        # Link Parsing
        linked_issue_keys = [link['outwardIssue']['key'] for link in fields.get('issuelinks', []) if 'outwardIssue' in link]
        linked_issue_keys.extend([link['inwardIssue']['key'] for link in fields.get('issuelinks', []) if 'inwardIssue' in link])
        linked_issues = ", ".join(linked_issue_keys)

        # Time Tracking (seconds)
        time_estimate = fields.get('timeoriginalestimate')
        
        # --- LOGIC FOR REPORTER/ASSIGNEE FALLBACK ---
        reporter_name = reporter_info.get('displayName')
        reporter_id = reporter_info.get('accountId')
        assignee_name = assignee_info.get('displayName')
        assignee_id = assignee_info.get('accountId')
        
        final_reporter_display = reporter_name or reporter_id or 'Unknown'
        final_assignee_display = assignee_name or assignee_id or 'Unassigned'
        
        # Issue Type (Defensive logic: ID fallback for name)
        issue_type_name = issuetype_info.get('name')
        issue_type_id = issuetype_info.get('id')
        final_issue_type_display = issue_type_name or issue_type_id or "N/A (Corrupt)"

        # --- NEW DATE EXTRACTION LOGIC ---
        created_datetime_str = fields.get('created', '')
        creation_date_only = 'N/A'
        creation_month = 'N/A'
        creation_year = 'N/A'

        if created_datetime_str:
            try:
                # Jira uses ISO format with milliseconds and timezone offset (2025-11-22T22:16:22.000-0300)
                # We simplify to the date part for parsing
                created_dt_obj = datetime.fromisoformat(created_datetime_str.split('.')[0])
                
                creation_date_only = created_dt_obj.strftime('%Y-%m-%d')
                creation_month = created_dt_obj.month    # Numeric month
                creation_year = created_dt_obj.year      # Numeric year
            except ValueError:
                # Fallback if parsing fails (e.g., corrupt date string)
                pass 
        # ----------------------------------


        rows.append({
            # --- IDENTIFICATION & METRICS CORE ---
            "Project Key": project_info.get('key', 'N/A'),
            "Key": key,
            "Issue Type": final_issue_type_display, 
            "Summary": fields.get('summary', 'No Summary'),
            
            # --- DATE METRICS (NEW) ---
            "Creation Date": creation_date_only,        # Standard Date (YYYY-MM-DD)
            "Creation Month": creation_month,           # New
            "Creation Year": creation_year,             # New
            "Updated": fields.get('updated', 'N/A').split('T')[0],
            
            # --- PEOPLE & ROLES ---
            "Reporter Name": final_reporter_display,
            "Reporter AccountID": reporter_id or 'N/A',
            "Assignee Name": final_assignee_display,
            "Assignee AccountID": assignee_id or 'N/A',
            
            # --- STATUS & PRIORITIES ---
            "Status": fields.get('status', {}).get('name', 'N/A'),
            "Priority": priority_info.get('name', 'Normal'),
            "Resolution": resolution_info.get('name', 'Unresolved'),

            # --- GROUPERS & LINKS ---
            "Components": components,
            "Labels": labels,
            "Fix Versions": fix_versions,
            "Linked Issues (Keys)": linked_issues,
            "Original Estimate (s)": time_estimate if time_estimate is not None else 0,
            "Link": f"{JIRA_BASE_URL}/browse/{key}"
        })

    # ... (rest of the pandas code to save the file)
    df = pd.DataFrame(rows)
    
    try:
        df.to_excel(filename, index=False)
        print(f"SUCCESS: Excel saved to: {os.path.abspath(filename)}")
    except PermissionError:
        print("ERROR: Close the Excel file before running.")
    except Exception as e:
        print(f"CRITICAL EXCEL ERROR: {e}")
# ======================================================================
#                               MAIN
# ======================================================================

if __name__ == "__main__":
    print("\n=======================================================")
    print("   STRATEGY: AUTOMATIC DISCOVERY + PROJECT SWEEP")
    print("=======================================================")
    
    start_time = time.time()
    master_list = []
    
    # 1. Get dynamic list of projects
    projects_list = get_all_accessible_projects()
    
    if not projects_list:
        print("WARNING: No accessible projects found. Check permissions or connection.")
        exit()

    print("-------------------------------------------------------")
    
    # 2. Iterate automatically
    for i, proj_key in enumerate(projects_list, 1):
        print(f"[{i}/{len(projects_list)}] Processing {proj_key}...", end=" ", flush=True)
        
        issues = get_issues_from_project(proj_key)
        
        if issues:
            print(f"✅ {len(issues)} records retrieved.")
            master_list.extend(issues)
        else:
            print(f"⭕ (Empty or Access Denied)")

    # 3. Generate Final Report
    if master_list:
        print("\n-------------------------------------------------------")
        print(f"GLOBAL SUMMARY: {len(master_list)} total records retrieved from {len(projects_list)} projects.")
        generate_excel_report(master_list)
    else:
        print("\nWARNING: No data was retrieved.")
        
    print(f"Total time: {round(time.time() - start_time, 2)} seconds.")