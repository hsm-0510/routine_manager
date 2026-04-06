import json
import os

def serial_config_load(key=None, idNum=0):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, '..', '..', 'config/system_config.json')
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            devices = data.get("serial_device", [])
            
            if devices:
                device_info = devices[idNum]
                return device_info.get(key, f"Error: Key '{key}' not found.")
            else:
                return "Error: 'serial_device' list is empty."
            
    except FileNotFoundError:
        return f"Error: File not found at {file_path}"
    except (IndexError, AttributeError):
        return "Error: Unexpected JSON format."

def waveshare_config_load(key=None, idNum=0):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, '..', '..', 'config/system_config.json')
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            waveshare_module = data.get("waveshare_device", [])
            
            if waveshare_module:
                device_info = waveshare_module[idNum]
                return device_info.get(key, f"Error: Key '{key}' not fount")
            else:
                return "Error: 'waveshare_device' list is empty"
    except FileNotFoundError:
        return f"Error: File not found at {file_path}"
    except (IndexError, AttributeError):
        return "Error: Unexpected JSON format."

def opc_config_load(key=None, idNum=0):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, '..', '..', 'config/system_config.json')
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            opcServer = data.get("opc_server", [])
            
            if opcServer:
                device_info = opcServer[idNum]
                return device_info.get(key, f"Error: Key '{key}' not fount")
            else:
                return "Error: 'opc_server' list is empty"
    except FileNotFoundError:
        return f"Error: File not found at {file_path}"
    except (IndexError, AttributeError):
        return "Error: Unexpected JSON format."

def tcp_payload_config_load():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, '..', '..', 'config/tcp_payload.json')
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return f"Error: File not found at {file_path}"
    except (IndexError, AttributeError):
        return "Error: Unexpected JSON format."

def system_config_load():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, '..', '..', 'config/system_config.json')
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return f"Error: File not found at {file_path}"
    except (IndexError, AttributeError):
        return "Error: Unexpected JSON format."