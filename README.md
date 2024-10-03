## Build And Run
> If you don't have git installed in Pepper, you can clone this repo and use `scp` to upload files to your pepper robot.

Open a ssh connection to Pepper robot,  
  
To install dependencies, run
```sh
pip install -r requirements.txt
```
This project sends identified text to the server you provided in OpenAI format. Currently it sent to the server built using our another project [SkywardAI Voyager](https://github.com/skywardai/voyager) on an AWS EC2 server. 
  
Assume we've got the AWS EC2 Server address, run
```sh
python start.py --base-route "http://<address-of-ec2-server>/v1"
```
To start the service on pepper robot. **DO NOT** forget to add the `http` or `https` before address.  
> The service will automatically add `/chat/completions` in the end of provided `base-route`.

And after it outputs: `INF: Started, you can speek now`, just speak and wait for its response.  
## Output
The output is in the format of 
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
Which is easier to debug.
## Development Guide
* [start.py](./start.py): Anything related to initialize
* [module_speechrecognition.py](./module_speechrecognition.py): Anything related to speech recognition
* [module_receiver.py](./module_receiver.py): Receive from speech recognition, send request to LLM and speak out

`memory` in main function of `start.py` is for sending events between modules, search for `self.memory` in module files for usage.  
`myBroker` is necessary to build channel in python runtime, it's the basic of using `memory`.
## Notes
Advanced functions may require use different speech recognition models, a new file implement other libraries might required.  
Try use different LLM to test performance, also fine-tune the required information to models or add the documents to conversation context for response related to the project.