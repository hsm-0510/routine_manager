import json
import os

def serial_config_load(key=None, idNum=0):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, '..', '..', 'config/serial_config.json')
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

def main():
    print("null")
if __name__ == "__main__":
    main()