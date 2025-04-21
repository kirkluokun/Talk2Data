import json
import os
from typing import Dict, List, Tuple, Optional, Set

# --- Configuration ---
# Define relative paths to the JSON files
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPLAINED_JSON_PATH = os.path.join(CURRENT_DIR, "db_columns_explained.json")
NAMES_JSON_PATH = os.path.join(CURRENT_DIR, "db_columns_names.json")

# Simplified manual mappings (if needed for _match_financial_term logic)
MANUAL_MAPPINGS = {
    "归母净利润": "归属于母公司的净利润",
    "归属于母公司所有者的净利润": "归属于母公司的净利润",
    "归属于母公司股东的净利润": "归属于母公司的净利润",
    "归母净利": "归属于母公司的净利润",
    "归属于母公司净利": "归属于母公司的净利润"
}

# --- Helper Functions ---

def load_aliases_and_standards(explained_path: str) -> Tuple[Dict[str, str], Set[str]]:
    """Loads aliases and the set of standard terms from the explained JSON."""
    aliases = {}
    standard_terms = set()
    try:
        with open(explained_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and 'aliases' in data:
                alias_mapping = data['aliases']
                if isinstance(alias_mapping, dict):
                    for alias, std_name in alias_mapping.items():
                        if isinstance(std_name, str):
                            aliases[alias] = std_name
                            standard_terms.add(std_name) # Add standard name from mapping
                        else:
                            print(f"[Warning] Invalid standard name type for alias '{alias}': {type(std_name)}")
                else:
                     print(f"[Error] Expected 'aliases' key in {explained_path} to contain a dictionary.")
            else:
                print(f"[Error] Expected {explained_path} to be a JSON object with an 'aliases' key.")
    except FileNotFoundError:
         print(f"[Error] File not found: {explained_path}")
    except json.JSONDecodeError:
         print(f"[Error] Failed to decode JSON from {explained_path}")
    except Exception as e:
        print(f"[Error] Unexpected error loading {explained_path}: {e}")
    return aliases, standard_terms

def load_table_columns(names_path: str) -> Dict[str, List[str]]:
    """Loads table structure (table_name -> list_of_columns)."""
    table_columns = {}
    try:
        with open(names_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                for table_name, content in data.items():
                     if isinstance(content, dict) and "columns" in content and isinstance(content["columns"], list):
                         table_columns[table_name] = content["columns"]
                     else:
                         print(f"[Warning] Invalid structure for table '{table_name}' in {names_path}")
            else:
                 print(f"[Error] Expected {names_path} to be a JSON object.")
    except FileNotFoundError:
         print(f"[Error] File not found: {names_path}")
    except json.JSONDecodeError:
         print(f"[Error] Failed to decode JSON from {names_path}")
    except Exception as e:
        print(f"[Error] Unexpected error loading {names_path}: {e}")
    return table_columns

def add_all_columns_to_standards(table_columns: Dict[str, List[str]], standard_terms: Set[str]):
    """Adds all actual column names to the standard terms set for robustness."""
    for columns in table_columns.values():
        for col in columns:
            standard_terms.add(col)


def match_financial_term(
    term: str,
    aliases: Dict[str, str],
    standard_terms: Set[str],
    manual_mappings: Dict[str, str]
) -> str:
    """Simplified term matching logic (prioritizes aliases)."""
    # 1. Manual mappings
    if term in manual_mappings:
        return manual_mappings[term]
    # 2. Aliases (prioritized)
    if term in aliases:
        return aliases[term]
    # 3. Standard terms
    if term in standard_terms:
        return term
    # 4. Fallback
    return term

def get_table_for_column(column_name: str, table_columns: Dict[str, List[str]]) -> Optional[str]:
    """Finds the table for a given column name."""
    for table_name, columns in table_columns.items():
        if column_name in columns:
            return table_name
    return None

# --- Main Test Logic ---

if __name__ == "__main__":
    print("Starting Comprehensive Alias Validation Test...")

    # 1. Load data
    aliases, standard_terms = load_aliases_and_standards(EXPLAINED_JSON_PATH)
    table_columns = load_table_columns(NAMES_JSON_PATH)
    add_all_columns_to_standards(table_columns, standard_terms) # Ensure all real columns are 'standard'

    if not aliases or not table_columns:
        print("\nCritical error during data loading. Aborting test.")
    else:
        print(f"Loaded {len(aliases)} aliases and {len(table_columns)} tables.")
        problematic_aliases = []
        total_checked = 0

        # 2. Iterate through all aliases
        for alias, expected_std_name in aliases.items():
            total_checked += 1
            issues = []

            # Perform matching
            actual_std_name = match_financial_term(alias, aliases, standard_terms, MANUAL_MAPPINGS)

            # Check 1: Standardization Accuracy
            if actual_std_name != expected_std_name:
                issues.append(f"标准化错误 (期望: '{expected_std_name}', 实际: '{actual_std_name}')")

            # Check 2: Actual Lookup Feasibility
            actual_table_name = get_table_for_column(actual_std_name, table_columns)
            if actual_table_name is None:
                issues.append(f"实际查找失败 (用 '{actual_std_name}' 找不到表)")

            # Check 3: Expected Standard Name Validity
            expected_table_name = get_table_for_column(expected_std_name, table_columns)
            if expected_table_name is None:
                issues.append(f"期望标准名无效 ('{expected_std_name}' 在任何表中都找不到)")

            # Record if any issues found
            if issues:
                problematic_aliases.append({
                    "别名": alias,
                    "期望标准名": expected_std_name,
                    "实际匹配名": actual_std_name,
                    "实际找到的表": actual_table_name,
                    "期望标准名对应的表": expected_table_name,
                    "问题描述": issues
                })

        # 3. Report Results
        print(f"\n--- Validation Report ---")
        print(f"Total Aliases Checked: {total_checked}")
        print(f"Problematic Aliases Found: {len(problematic_aliases)}")

        if problematic_aliases:
            print("\nDetails of Problematic Aliases:")
            for i, problem in enumerate(problematic_aliases):
                print(f"\n{i+1}. 别名: '{problem['别名']}'")
                print(f"   - 期望标准名: '{problem['期望标准名']}'")
                print(f"   - 实际匹配名: '{problem['实际匹配名']}'")
                print(f"   - 实际找到的表: {problem['实际找到的表']}")
                print(f"   - 期望标准名对应的表: {problem['期望标准名对应的表']}")
                print(f"   - 问题:")
                for issue in problem['问题描述']:
                    print(f"     - {issue}")
        else:
            print("\nAll aliases appear to be mapped and resolvable correctly!")

    print("\nComprehensive Alias Validation Test Finished.") 