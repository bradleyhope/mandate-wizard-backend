#!/usr/bin/env python3
"""
Import collected data into Mandate Wizard system
"""

import json
import os
from datetime import datetime

def load_json_file(filepath):
    """Load and validate JSON file"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON syntax error: {e}"
    except FileNotFoundError:
        return None, f"File not found: {filepath}"
    except Exception as e:
        return None, f"Error: {e}"

def validate_layer3(data):
    """Validate Layer 3 (Production Companies) data"""
    errors = []
    companies = data.get('production_companies', [])
    
    if not companies:
        return ["No production companies found in file"]
    
    for i, company in enumerate(companies):
        required_fields = ['company_name', 'country', 'specializations', 'netflix_relationship', 'notable_projects']
        for field in required_fields:
            if field not in company:
                errors.append(f"Company {i+1}: Missing required field '{field}'")
        
        # Validate notable_projects has at least 2
        if len(company.get('notable_projects', [])) < 2:
            errors.append(f"Company {i+1} ({company.get('company_name')}): Needs at least 2 notable projects")
    
    return errors

def validate_layer4(data):
    """Validate Layer 4 (Recent Greenlights) data"""
    errors = []
    greenlights = data.get('greenlights', [])
    
    if not greenlights:
        return ["No greenlights found in file"]
    
    for i, greenlight in enumerate(greenlights):
        required_fields = ['project_title', 'executive_name', 'greenlight_date', 'announcement_date', 
                          'genre', 'format', 'production_company', 'source_url']
        for field in required_fields:
            if field not in greenlight or not greenlight[field]:
                errors.append(f"Greenlight {i+1}: Missing required field '{field}'")
        
        # Validate date format
        for date_field in ['greenlight_date', 'announcement_date']:
            date_str = greenlight.get(date_field, '')
            if date_str:
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    errors.append(f"Greenlight {i+1} ({greenlight.get('project_title')}): Invalid date format for '{date_field}' (use YYYY-MM-DD)")
    
    return errors

def validate_layer5(data):
    """Validate Layer 5 (Pitch Requirements) data"""
    errors = []
    requirements = data.get('pitch_requirements', [])
    
    if not requirements:
        return ["No pitch requirements found in file"]
    
    for i, req in enumerate(requirements):
        required_fields = ['executive_name', 'content_type', 'submission_process', 'required_materials', 'source_url']
        for field in required_fields:
            if field not in req:
                errors.append(f"Requirement {i+1}: Missing required field '{field}'")
        
        # Validate submission_process has at least 3 steps
        process = req.get('submission_process', {})
        if len(process) < 3:
            errors.append(f"Requirement {i+1} ({req.get('executive_name')}): Needs at least 3 steps in submission_process")
    
    return errors

def import_data():
    """Main import function"""
    print("=" * 70)
    print("MANDATE WIZARD DATA IMPORT")
    print("=" * 70)
    
    data_dir = "/home/ubuntu/mandate_wizard_web_app/data"
    
    layers = {
        "Layer 3 (Production Companies)": {
            "file": f"{data_dir}/production_companies.json",
            "validator": validate_layer3
        },
        "Layer 4 (Recent Greenlights)": {
            "file": f"{data_dir}/recent_greenlights.json",
            "validator": validate_layer4
        },
        "Layer 5 (Pitch Requirements)": {
            "file": f"{data_dir}/pitch_requirements.json",
            "validator": validate_layer5
        },
        "Layer 6 (Packaging Intelligence)": {
            "file": f"{data_dir}/packaging_intelligence.json",
            "validator": None  # Add validator if needed
        },
        "Layer 7 (Timing & Strategy)": {
            "file": f"{data_dir}/timing_strategy.json",
            "validator": None  # Add validator if needed
        }
    }
    
    results = {
        "success": [],
        "warnings": [],
        "errors": []
    }
    
    for layer_name, layer_info in layers.items():
        print(f"\n{layer_name}")
        print("-" * 70)
        
        # Load file
        data, error = load_json_file(layer_info['file'])
        if error:
            print(f"❌ {error}")
            results['errors'].append(f"{layer_name}: {error}")
            continue
        
        print(f"✅ File loaded successfully")
        
        # Count entries
        if layer_name == "Layer 3 (Production Companies)":
            count = len(data.get('production_companies', []))
        elif layer_name == "Layer 4 (Recent Greenlights)":
            count = len(data.get('greenlights', []))
        elif layer_name == "Layer 5 (Pitch Requirements)":
            count = len(data.get('pitch_requirements', []))
        elif layer_name == "Layer 6 (Packaging Intelligence)":
            count = len(data.get('packaging_intelligence', []))
        elif layer_name == "Layer 7 (Timing & Strategy)":
            count = len(data.get('timing_strategy', {}).get('industry_events', []))
        else:
            count = 0
        
        print(f"📊 Entries found: {count}")
        
        # Validate
        if layer_info['validator']:
            validation_errors = layer_info['validator'](data)
            if validation_errors:
                print(f"⚠️  Validation warnings:")
                for err in validation_errors[:5]:  # Show first 5 errors
                    print(f"   - {err}")
                if len(validation_errors) > 5:
                    print(f"   ... and {len(validation_errors) - 5} more")
                results['warnings'].append(f"{layer_name}: {len(validation_errors)} validation issues")
            else:
                print(f"✅ Validation passed")
                results['success'].append(layer_name)
        else:
            print(f"⚠️  No validator available (skipping validation)")
            results['success'].append(layer_name)
    
    # Summary
    print("\n" + "=" * 70)
    print("IMPORT SUMMARY")
    print("=" * 70)
    print(f"✅ Successful: {len(results['success'])}")
    print(f"⚠️  Warnings: {len(results['warnings'])}")
    print(f"❌ Errors: {len(results['errors'])}")
    
    if results['warnings']:
        print("\nWarnings:")
        for warning in results['warnings']:
            print(f"  - {warning}")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\n" + "=" * 70)
    print("Next steps:")
    print("1. Fix any validation errors in the JSON files")
    print("2. Re-run this script to verify")
    print("3. Restart Flask server to load new data")
    print("=" * 70)

if __name__ == "__main__":
    import_data()

