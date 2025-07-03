"""
Script to merge YAML files by copying base.yml and updating provider_id from temp.yml
"""

import yaml
import sys
from pathlib import Path

def find_provider_id_in_dict(data, provider_id=None):
    """
    Recursively search for provider_id in nested dictionary/list structures
    """
    if isinstance(data, dict):
        if 'provider_id' in data:
            return data['provider_id']
        for value in data.values():
            result = find_provider_id_in_dict(value, provider_id)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_provider_id_in_dict(item, provider_id)
            if result:
                return result
    return None

def update_provider_id_in_dict(data, new_provider_id):
    """
    Recursively update all provider_id occurrences in nested dictionary/list structures
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'provider_id':
                data[key] = new_provider_id
            else:
                update_provider_id_in_dict(value, new_provider_id)
    elif isinstance(data, list):
        for item in data:
            update_provider_id_in_dict(item, new_provider_id)

def main():
    # File paths
    base_file = Path('base.yml')
    temp_file = Path('temp.yml')
    output_file = Path('Travel Agent.yml')
    
    # Check if files exist
    if not base_file.exists():
        print(f"Error: {base_file} not found!")
        sys.exit(1)
    
    if not temp_file.exists():
        print(f"Error: {temp_file} not found!")
        sys.exit(1)
    
    try:
        # Read base.yml
        print(f"Reading {base_file}...")
        with open(base_file, 'r', encoding='utf-8') as f:
            base_data = yaml.safe_load(f)
        
        # Read temp.yml
        print(f"Reading {temp_file}...")
        with open(temp_file, 'r', encoding='utf-8') as f:
            temp_data = yaml.safe_load(f)
        
        # Find provider_id in temp.yml
        temp_provider_id = find_provider_id_in_dict(temp_data)
        
        if not temp_provider_id:
            print("Error: Could not find provider_id in temp.yml!")
            sys.exit(1)
        
        print(f"Found provider_id in temp.yml: {temp_provider_id}")
        
        # Update provider_id in base_data
        update_provider_id_in_dict(base_data, temp_provider_id)
        
        # Write the new file
        print(f"Writing merged data to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(base_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print(f"Successfully created {output_file} with provider_id: {temp_provider_id}")
        
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"File error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()