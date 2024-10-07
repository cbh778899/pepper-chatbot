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
    
def request(base_url, route, body, headers = {}, is_json = True):
    if is_json:
        body = json.dumps(body)
    
    req = urllib2.Request(base_url+route, data=body)
    
    if 'Content-Type' not in headers:
        req.add_header('Content-Type', 'application/json')

    for k, v in headers:
        req.add_header(k, v)

    try:
        response = urllib2.urlopen(req)
        response_data = response.read()
        return json.loads(response_data)
    
    except urllib2.HTTPError as e:
        print("HTTP Error:", e.code, e.read())

    except urllib2.URLError as e:
        print("URL Error:", e.reason)


def chat_completion(base_url, messages, max_tokens=50, route='/chat/completions', model_name=None, api_key=None):
    data = {
        'messages': messages,
        'max_tokens': max_tokens
    }
    if model_name: data['model'] = model_name

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
            recoginzed_text = resp['text']
        elif 'error' in resp:
            print('Error: '+resp['error'])
    
    return recoginzed_text