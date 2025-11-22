 Jira Xray Bulk Data ExtractorThis project provides a robust Python solution for extracting comprehensive issue and testing metadata from large, fragmented Jira Cloud instances. 
 
 It utilizes advanced Keyset/ID pagination to bypass standard API rate limits and indexing failures, ensuring a complete and accurate data dump for Business Intelligence (BI) and metrics analysis.FeaturesFull Project Discovery: Automatically queries the Jira API to discover all projects accessible by the authenticated user.Stable Data Extraction (Keyset Pagination): Uses the ORDER BY id DESC filtering strategy instead of the unstable startAt (offset) parameter, preventing infinite loops and data loss common in enterprise Jira environments.Granular Metrics: Extracts key fields for QA and development metrics, including Issue Type, Reporter, Assignee, Priority, Resolution, Time Estimate, and Linked 
 
 Issues.Error Handling: Includes robust error checks for API access denial (401/403) and safe handling of missing user data (using accountId as a fallback for 'Unknown' names).Clean Output: Generates a single, consolidated .xlsx file ready for use in Pandas, Excel, or Power BI.🛠️ Setup and Installation1. PrerequisitesEnsure you have Python 3.8+ installed
 Bash# Install required Python libraries
pip install requests pandas openpyxl

2. Configuration (Environment Variables)The script relies on the following environment variables for authentication. These must be set in your operating system (or in a separate .env file that you load).VariablePurposeValue ExampleJIRA_EMAILYour Atlassian email address.user@bancoicbc.com.arJIRA_API_TOKENYour Atlassian API Token (generated in your Atlassian Profile).ATATT3xFf...JIRA_BASE_URLThe base URL of your Jira instance (used internally).https://bancoicbc.atlassian.netPROXY_URL (Optional)Required if accessing Jira through a corporate firewall/proxy.http://proxy.corp:80803. ExecutionActivate your virtual environment and run the main script:Bash# Activate your virtual environment
source venv/bin/activate  # macOS/Linux
# OR
# .\venv\Scripts\activate # Windows PowerShell

# Run the script
python jira_xray_bulk_data_extractor.py
🚀 Usage and OutputConsole OutputThe script will first query your project list, then iterate through each one, providing progress feedback:SUCCESS: Found 45 accessible projects.
-------------------------------------------------------
[1/45] Processing UPMU... ✅ 1826 records retrieved.
[2/45] Processing SDI... ✅ 14500 records retrieved.
[3/45] Processing MBD... ⭕ (Empty or Access Denied)
...
GLOBAL SUMMARY: 26759 total records retrieved from 45 projects.
INFO: Generating Master Excel Report with 26759 records...
SUCCESS: Excel saved to: /path/to/project/consolidated_report.xlsx
Key Report ColumnsThe output file, consolidated_report.xlsx, includes the following essential columns for filtering and metric calculation:Column NameData PurposeExample OutputProject KeyPrimary filter for teams/modules.SDIIssue TypeDistinguishes Test vs Story vs Test Plan.Test ExecutionReporter NameUser who created the ticket.Sergio Moramarco Reporter AccountIDPermanent unique identifier (used as fallback for 'Unknown').557058:...StatusCurrent workflow state.In ProgressPriorityBusiness impact level.HighestOriginal Estimate (s)Time tracking data (in seconds).3600Linked Issues (Keys)Requirements or Bugs related to this issue.REQ-400, BUG-105CreatedDate of creation.2025-10-25