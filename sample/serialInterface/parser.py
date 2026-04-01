from sample.serialInterface import commands

# Sample Data (hex): b'\x02AA00\x03'
def parse_handshakeResponse(response):
    try:
        return response[1:5]
    except Exception as e:
        print(f"Could not parse handshake response: {e}")

# Sample Data (hex): b'\x02AB+000000018\x03'
def parse_indicatorAddress(response):
    try:
        return response[1:2]
    except Exception as e:
        print(f"Could not parse indicator address: {e}")

# Sample Data (hex): b'\x02AB+000000018\x03'
def parse_signBit(response):
    try:
        return response[3:4]
    except Exception as e:
        print(f"Could not parse sign bit: {e}")

# Sample Data (hex): b'\x02AB+000000018\x03'
def parse_grossWeight(response, sign, decimalPoint):
    try:
        if sign == b'+':
            parsedResponse = int(response[4:10])
        elif sign == b'-':
            parsedResponse = -1 * int(response[4:10])
        else:
            parsedResponse = "error"
            
        return float(parsedResponse)/(10**decimalPoint)
    except Exception as e:
        print(f"Could not parse gross weight: {e}")

# Sample Data (hex): b'\x02AB+000000018\x03'
def parse_decimalPoints(response):
    # Check if response is empty or too short
    if not response or len(response) < 11:
        print("Warning: Received incomplete or empty serial data.")
        return 0.0 # Or handle as an error  
    try:
        return float(response[10:11])
    except ValueError:
        print(f"Error: Could not convert {response[10:11]} to float")
        return 0.0