## Build And Run
> If you don't have git installed in Pepper, you can clone this repo and use `scp` to upload files to your pepper robot.

Open a ssh connection to Pepper robot,  
  
To install dependencies, run
```sh
pip install -r requirements.txt
```
This project sends identified text to the server you provided in OpenAI format. Currently it sent to the server built using our another project [SkywardAI pepper-voyager](https://github.com/SkywardAI/pepper-voyager) on an AWS EC2 server. 
  
Assume we've got the AWS EC2 Server address, run
```sh
python start.py --base-route "http://<address-of-ec2-server>/v1"
```
To start the service on pepper robot. **DO NOT** forget to add the `http` or `https` before address.  
> The service will automatically add `/chat/completions` in the end of provided `base-route`.

And after it outputs: `INF: Started, you can speek now`, just speak and wait for its response.  
## Output
The terminal output is in the format of 
```
Speech Recognition Result:
================================
hi how are you
================================

AI Inference Result:
================================
Hello! As an AI assistant, I don't have feelings, but I'm operating properly and ready to help you with any questions or tasks you may have. How can I assist you today?
================================

```
You can also save the conversation to a `csv` file, see [Flags](#flags)
## .env
You can add a `.env` file to add more control  
Available fields are listed below:
* `NAO_IP` - **String**: The IP address of Pepper Robot, default `localhost`
* `NAO_PORT` - **Integer**: The port of Pepper Robot, default `9559`
* `URL` - **String**: The url of AI Chat Completion server, **required**
* `CHAT_COMPLETION_ROUTE` - **String**: The route of AI Completion based on provided route, default `/chat/completions`
* `MODEL_NAME` - **String**: The model name when integrate with OpenAI, for example, `gpt-4o`
* `API_KEY` - **String**: The API Key of OpenAI API, sent in `Authorization` header
* `HOLD_TIME` - **Float**: Minimum recording time in seconds. Default `2.0`
* `RELEASE_TIME` - **Float**: Time idle after stopped recording each piece in seconds. Default `1.0`
* `RECORD_DURATION` - **Float**: Maximum recording time in seconds. Default `7.0` 
* `LOOK_AHEAD_DURATION` - **Float**: Amount of seconds before the threshold trigger that will be included in the request. Default `0.5`
* `AUTO_DETECTION_THREADSHOLD` - **Integer**: Threadshold of autodetection. Default `5`
## Flags
There are some flags you can set when running, available flags are listed below:
* `--ip`: Specify the IP Address of Pepper robot, default `localhost`
* `--port`: Specify the port of Pepper robot, default `9559`
* `--url`: Specify the url of AI Chat Completions server. Either set it here or in `.env` file
* `--route`: Specify the route of AI Chat Completions based on server, default `/chat/completions`
* `--api-key`: Specify the OpenAI API Key
* `--model-name`: Specify the OpenAI model name
* `--save-csv`: Set to save conversation to `dialogue.csv`
### Example Usage:
```sh
python start.py --url "http://<ec2-instance-public-DNS>/v1" --save-csv
```
## Development Guide
* [start.py](./start.py): Anything related to initialize
* [module_speechrecognition.py](./module_speechrecognition.py): Anything related to speech recognition
* [module_receiver.py](./module_receiver.py): Receive from speech recognition, send request to LLM and speak out

`memory` in main function of `start.py` is for sending events between modules, search for `self.memory` in module files for usage.  
`myBroker` is necessary to build channel in python runtime, it's the basic of using `memory`.
## Notes
Advanced functions may require use different speech recognition models, a new file implement other libraries might required.  
Try use different LLM to test performance, also fine-tune the required information to models or add the documents to conversation context for response related to the project.