#!/usr/bin/env python3
"""
Test script for the Inference API

This demonstrates how to call the new inference endpoint to:
1. Trigger drift analysis
2. Get results in a single API call

Usage:
    python test_inference_api.py
"""

import requests
import json
import sys

# API Configuration
API_URL = "http://localhost:3000/api/inference"

def test_inference_api(service_name: str, environment: str):
    """
    Test the inference API with given service and environment
    
    Args:
        service_name: Service identifier (e.g., 'cxp_ptg_adapter')
        environment: Environment to analyze (e.g., 'alpha', 'beta1', 'prod')
    """
    print("=" * 80)
    print("🤖 Testing Inference API")
    print("=" * 80)
    print(f"📋 Service: {service_name}")
    print(f"🌍 Environment: {environment}")
    print(f"🌐 API URL: {API_URL}")
    print("=" * 80)
    
    # Prepare request payload
    payload = {
        "service_name": service_name,
        "environment": environment
    }
    
    print("\n📤 Sending request...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        # Make API call
        response = requests.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check response
        if response.status_code == 200:
            print("✅ SUCCESS!")
            print("=" * 80)
            
            result = response.json()
            
            # Display metadata summary
            print("\n📊 Analysis Results:")
            print("-" * 80)
            print(f"Service:          {result.get('service_name', 'N/A')}")
            print(f"Environment:      {result.get('environment', 'N/A')}")
            print(f"Run ID:           {result.get('run_id', 'N/A')}")
            print(f"Timestamp:        {result.get('timestamp', 'N/A')}")
            print(f"Execution Time:   {result.get('execution_time_seconds', 0):.2f}s")
            
            metrics = result.get('metrics', {})
            print(f"\n📁 File Analysis:")
            print(f"Total Config Files:    {metrics.get('total_config_files', 0)}")
            print(f"Files with Drift:      {metrics.get('files_with_drift', 0)}")
            
            print(f"\n🔍 Drift Breakdown:")
            print(f"Total Drifts:          {metrics.get('total_drifts', 0)}")
            print(f"   ├─ ⚠️  High Risk:    {metrics.get('high_risk_drifts', 0)}")
            print(f"   ├─ ⚡ Medium Risk:   {metrics.get('medium_risk_drifts', 0)}")
            print(f"   ├─ ℹ️  Low Risk:     {metrics.get('low_risk_drifts', 0)}")
            print(f"   └─ ✅ Allowed:       {metrics.get('allowed_variance', 0)}")
            
            print(f"\n🎯 Overall Risk Level: {metrics.get('overall_risk_level', 'N/A')}")
            
            analysis_url = result.get('analysis_url', 'N/A')
            print(f"\n🔗 View Full Details:")
            print(f"   {analysis_url}")
            print("-" * 80)
            
            # Save full response to file
            output_file = f"inference_result_{service_name}_{environment}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Full response saved to: {output_file}")
            
            return True
            
        else:
            print(f"❌ FAILED - Status Code: {response.status_code}")
            print("=" * 80)
            print("Error Response:")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR")
        print("=" * 80)
        print("Could not connect to the API server.")
        print("Make sure the server is running on localhost:3000")
        print("\nStart the server with:")
        print("  cd /Users/jayeshzambre/Downloads/AI\\ Project/strands-multi-agent-system")
        print("  python main.py")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False


def main():
    """Run inference API tests"""
    print("\n🚀 Inference API Test Suite")
    print("=" * 80)
    
    # Test cases
    test_cases = [
        ("cxp_ptg_adapter", "alpha"),
        ("cxp_ptg_adapter", "beta1"),
        # Add more test cases as needed
    ]
    
    # You can also get input from command line
    if len(sys.argv) == 3:
        service_name = sys.argv[1]
        environment = sys.argv[2]
        print(f"Using command-line arguments: {service_name}, {environment}\n")
        test_inference_api(service_name, environment)
    else:
        # Run default test case
        print("Running default test case...\n")
        service_name, environment = test_cases[0]
        test_inference_api(service_name, environment)
        
        print("\n" + "=" * 80)
        print("💡 TIP: You can specify custom service and environment:")
        print(f"   python test_inference_api.py <service_name> <environment>")
        print("\nExamples:")
        print("   python test_inference_api.py cxp_ptg_adapter alpha")
        print("   python test_inference_api.py cxp_ptg_adapter beta1")
        print("   python test_inference_api.py cxp_ptg_adapter prod")


if __name__ == "__main__":
    main()

