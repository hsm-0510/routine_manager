from sample.serialInterface import commands

# Sample Data (hex): b'\x02AA00\x03'
def parse_handshakeResponse(response):
    return response[1:5]

# Sample Data (hex): b'\x02AB+000000018\x03'
def parse_indicatorAddress(response):
    return response[1:2]

# Sample Data (hex): b'\x02AB+000000018\x03'
def parse_signBit(response):
    return response[3:4]

# Sample Data (hex): b'\x02AB+000000018\x03'
def parse_grossWeight(response, sign, decimalPoint):
    if sign == b'+':
        parsedResponse = int(response[4:10])
    elif sign == b'-':
        parsedResponse = -1 * int(response[4:10])
    else:
        parsedResponse = "error"
        
    return float(parsedResponse)/(10**decimalPoint)

# Sample Data (hex): b'\x02AB+000000018\x03'
def parse_decimalPoints(response):
    parsedResponse = float(response[10:11])
    return parsedResponse