import os
import urllib2
import json
import io
import wave
import struct

def load_env(file_path = '.env'):
    try:
        with open(file_path, 'r') as f:
            line = f.readline()
            while line:
                line = line.strip()
                
                if line and not line.startswith('#'):
                    if '=' in line:
                        k, v = line.split('=')
                        os.environ[k.strip()] = v.strip()

                line = f.readline()
            f.close()
    except:
        return

def toint(int_like):
    try:
        i = int(int_like)
        return i
    except:
        return 0
    
def tofloat(float_like):
    try:
        f = float(float_like)
        return f
    except:
        return 0
    
def request(base_url, route, body, headers = {}, is_json = True):
    if is_json:
        body = json.dumps(body)
    
    req = urllib2.Request(base_url+route, data=body)
    
    if 'Content-Type' not in headers:
        req.add_header('Content-Type', 'application/json')

    for k, v in headers.items():
        req.add_header(k, v)

    try:
        response = urllib2.urlopen(req)
        response_data = response.read()
        return json.loads(response_data)
    
    except urllib2.HTTPError as e:
        print("HTTP Error:", e.code, e.read())

    except urllib2.URLError as e:
        print("URL Error:", e.reason)


def chat_completion(base_url, messages, max_tokens=0, route='/chat/completions', model_name=None, api_key=None):
    data = {
        'messages': messages,
    }
    if model_name: data['model'] = model_name
    if max_tokens: data['max_tokens'] = max_tokens

    resp = request(base_url, route, data, {'Authorization': 'Bearer '+ (api_key or 'no-key')})
    resp_text = str(resp['choices'][0]['message']['content']) if resp else ''
   
    return resp_text

def audio_recoginze(base_url, data, route='/speech/recognition', api_key='no-key'):
    resp = request(
        base_url, route, data, is_json=False,
        headers={
            'Content-Type': 'audio/wav',
            'Authorization': 'Bearer '+ (api_key or 'no-key')
        }
    )
    recoginzed_text = ''

    if resp:
        if 'text' in resp:
            recoginzed_text = str(resp['text'])
        elif 'error' in resp:
            print('Error: '+resp['error'])
    
    return recoginzed_text

def buffer_to_wav_in_memory(buffer, sample_rate=48000, num_channels=1, sampwidth=2):
    # Ensure that the buffer length matches the expected size for the sample width
    if sampwidth == 2:
        # Expect buffer to be a list of 16-bit PCM samples (signed integers)
        expected_len = len(buffer)
        if expected_len % num_channels != 0:
            raise ValueError("Buffer length is not divisible by the number of channels")
        
        # Convert the buffer into the proper format
        # '<h' means little-endian ('<') 16-bit signed integers ('h')
        buffer_bytes = struct.pack('<' + 'h' * expected_len, *buffer)
    else:
        raise ValueError("Unsupported sample width")

    # Create an in-memory buffer for the WAV file
    byte_io = io.BytesIO()

    # Open the WAV file for writing (Python 2.7 does not support 'with' context for wave module)
    wav_file = wave.open(byte_io, 'wb')
    
    # Set the number of channels, sample width, and frame rate
    wav_file.setnchannels(num_channels)  # Mono = 1, Stereo = 2
    wav_file.setsampwidth(sampwidth)     # Sample width in bytes (2 for 16-bit PCM)
    wav_file.setframerate(sample_rate)   # Samples per second

    # Write the PCM data to the in-memory file
    wav_file.writeframes(buffer_bytes)
    
    # Close the WAV file manually
    wav_file.close()

    # Get the WAV file as a byte string
    byte_io.seek(0)
    return byte_io.read()