import requests
import json
import time
import random
from datetime import datetime

# Configuration
BACKEND_URL = "http://127.0.0.1:8000/logs"
API_KEY = "supersecretapikey"

# Normal baseline processes
NORMAL_PROCESSES = [
    'chrome.exe', 'Code.exe', 'svchost.exe', 'explorer.exe', 'msedge.exe',
    'python.exe', 'AnyDesk.exe', 'SecurityHealthSystray.exe', 'Taskmgr.exe',
    'notepad.exe', 'winlogon.exe', 'csrss.exe', 'services.exe', 'lsass.exe',
    'smss.exe', 'dwm.exe', 'fontdrvhost.exe', 'RuntimeBroker.exe'
] * 5  # Expanded list

SUSPICIOUS_PROCESSES = [
    'bitcoin_miner.exe', 'ransomware.exe', 'keylogger.exe', 'backdoor.exe',
    'crypto_locker.exe', 'trojan.exe', 'worm.exe', 'spyware.exe',
    'malware.exe', 'rootkit.exe', 'botnet.exe', 'adware.exe'
]

def create_normal_log():
    """Create a normal system log"""
    sample_size = min(random.randint(250, 300), len(NORMAL_PROCESSES))
    
    return {
        "hostname": "DESKTOP-CHBR0NO",
        "processes": random.sample(NORMAL_PROCESSES, sample_size),
        "total_memory": 17015463936,
        "used_memory": random.randint(10000000000, 11000000000),
        "network_received": random.randint(0, 1000),
        "network_transmitted": random.randint(0, 1000),
        "cpu_usage": random.uniform(0, 30),
        "timestamp": int(datetime.now().timestamp())
    }

def create_memory_anomaly_log():
    """Create log with extremely high memory usage"""
    log = create_normal_log()
    log["used_memory"] = 16000000000  # 94% memory usage
    log["processes"].extend(random.sample(SUSPICIOUS_PROCESSES, 3))
    return log

def create_process_anomaly_log():
    """Create log with suspicious process count"""
    log = create_normal_log()
    additional_processes = SUSPICIOUS_PROCESSES + [f"malware_{i}.exe" for i in range(200)]
    log["processes"].extend(additional_processes)
    log["processes"] = log["processes"][:500]  # Cap at 500 processes
    return log

def create_cpu_anomaly_log():
    """Create log with extremely high CPU usage"""
    log = create_normal_log()
    log["cpu_usage"] = 98.5
    log["processes"].extend(["bitcoin_miner.exe", "crypto_miner.exe"])
    return log

def create_low_process_anomaly_log():
    """Create log with suspiciously low process count"""
    return {
        "hostname": "DESKTOP-CHBR0NO",
        "processes": random.sample(NORMAL_PROCESSES, 5),
        "total_memory": 17015463936,
        "used_memory": 15000000000,
        "network_received": 0,
        "network_transmitted": 0,
        "cpu_usage": 5.0,
        "timestamp": int(datetime.now().timestamp())
    }

def create_network_anomaly_log():
    """Create log with high network activity"""
    log = create_normal_log()
    log["network_received"] = 100000000
    log["network_transmitted"] = 50000000
    log["processes"].extend(["data_exfil.exe", "backdoor.exe"])
    return log

def send_log(log_data, test_name):
    """Send log to backend"""
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"\n🚀 Sending {test_name}...")
    print(f"📊 Memory: {(log_data['used_memory'] / log_data['total_memory']) * 100:.1f}%")
    print(f"🖥️  Processes: {len(log_data['processes'])}")
    print(f"⚡ CPU: {log_data['cpu_usage']:.1f}%")
    print(f"🌐 Network: RX={log_data['network_received']} TX={log_data['network_transmitted']}")
    
    try:
        response = requests.post(BACKEND_URL, json=log_data, headers=headers, timeout=10)
        print(f"✅ Response: {response.status_code}")
        if response.status_code == 202:
            result = response.json()
            print(f"📨 Accepted: {result.get('accepted', 'N/A')} logs")
            print(f"💾 Buffer: {result.get('buffer_size', 'N/A')} logs")
            print(f"🤖 Model trained: {result.get('model_trained', 'N/A')}")
        return response.json()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_sequence():
    """Run a sequence of tests"""
    print("🔍 Starting Anomaly Detection Tests")
    print("=" * 50)
    
    tests = [
        ("NORMAL LOG", create_normal_log),
        ("MEMORY ANOMALY (94% usage)", create_memory_anomaly_log),
        ("PROCESS ANOMALY (400+ processes)", create_process_anomaly_log),
        ("CPU ANOMALY (98.5% usage)", create_cpu_anomaly_log),
        ("LOW PROCESS ANOMALY (malware hiding)", create_low_process_anomaly_log),
        ("NETWORK ANOMALY (data exfiltration)", create_network_anomaly_log)
    ]
    
    for test_name, test_func in tests:
        send_log(test_func(), test_name)
        time.sleep(2)

def interactive_test():
    """Interactive testing mode"""
    print("\n🎮 Interactive Anomaly Testing")
    
    tests = {
        "1": ("Memory Anomaly (High usage)", create_memory_anomaly_log),
        "2": ("Process Anomaly (Too many processes)", create_process_anomaly_log),
        "3": ("CPU Anomaly (High CPU)", create_cpu_anomaly_log),
        "4": ("Low Process Anomaly (Malware hiding)", create_low_process_anomaly_log),
        "5": ("Network Anomaly (Data transfer)", create_network_anomaly_log),
        "6": ("Normal Log (Baseline)", create_normal_log),
        "7": ("Continuous Test (Send all types)", None)
    }
    
    for key, (description, _) in tests.items():
        print(f"{key}. {description}")
    
    choice = input("\nEnter choice (1-7): ").strip()
    
    if choice == "7":
        test_sequence()
    elif choice in tests:
        test_name, test_func = tests[choice]
        send_log(test_func(), test_name)
    else:
        print("Invalid choice")

if __name__ == "__main__":
    print("🚨 Anomaly Detection Tester")
    print("Make sure your backend is running on http://127.0.0.1:8000")
    
    mode = input("Choose mode: (1) Interactive (2) Auto-sequence [1]: ").strip() or "1"
    
    if mode == "1":
        interactive_test()
    else:
        test_sequence()
    
    print("\nTesting completed! Check your backend logs for detection results.")