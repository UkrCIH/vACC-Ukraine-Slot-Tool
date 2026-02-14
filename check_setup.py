#!/usr/bin/env python3


import os
import sys

def check_file_structure():
    print("=" * 60)
    print("Flight Departure Tracking System - Setup Check")
    print("=" * 60)
    print()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Current directory: {current_dir}")
    print()
    
    all_good = True
    
    # Check for server.py
    if os.path.exists(os.path.join(current_dir, 'server.py')):
        print("✓ server.py found")
    else:
        print("✗ server.py NOT FOUND")
        all_good = False
    
    # Check for templates folder
    templates_dir = os.path.join(current_dir, 'templates')
    if os.path.exists(templates_dir):
        print("✓ templates folder found")
        
        # Check for individual template files
        required_templates = ['pilot.html', 'atc_login.html', 'atc.html']
        for template in required_templates:
            template_path = os.path.join(templates_dir, template)
            if os.path.exists(template_path):
                print(f"  ✓ {template} found")
            else:
                print(f"  ✗ {template} NOT FOUND")
                all_good = False
    else:
        print("✗ templates folder NOT FOUND")
        all_good = False
    
    print()
    print("=" * 60)
    
    if all_good:
        print("✓ ALL FILES PRESENT - Ready to run!")
        print("=" * 60)
        print()
        print("To start the server:")
        print("  Linux/Mac: ./start_server.sh")
        print("  Windows:   start_server.bat")
        print("  Manual:    python server.py")
        return True
    else:
        print("✗ MISSING FILES - Please ensure you have:")
        print("=" * 60)
        print()
        print("Required structure:")
        print("  your-folder/")
        print("  ├── server.py")
        print("  ├── start_server.sh (or .bat)")
        print("  └── templates/")
        print("      ├── pilot.html")
        print("      ├── atc_login.html")
        print("      └── atc.html")
        print()
        print("Make sure you downloaded ALL files and the templates folder!")
        return False

if __name__ == '__main__':
    success = check_file_structure()
    sys.exit(0 if success else 1)
