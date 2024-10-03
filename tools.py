import os
import urllib2
import json

def load_env(file_path = '.env'):
    try:
        with open(file_path, 'r') as f:
            line = f.readline()
            while line:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue

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

def chat_completion(base_url, messages, max_tokens=50, route='/chat/completions', model_name=None, api_key=None):
    data = {
        'messages': messages,
        'max_tokens': max_tokens
    }
    if model_name: data['model'] = model_name

    data = json.dumps(data)
    req = urllib2.Request(base_url+route, data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', 'Bearer '+ (api_key or 'no-key'))

    try:
        # Send the request and get the response
        response = urllib2.urlopen(req)
        
        # Read and parse the response
        response_data = response.read()
        parsed_response = json.loads(response_data)
        
        # Print the parsed response
        resp_text = str(parsed_response['choices'][0]['message']['content'])
        return resp_text 

    except urllib2.HTTPError as e:
        print("HTTP Error:", e.code, e.read())
        return ''

    except urllib2.URLError as e:
        print("URL Error:", e.reason)
        return ''