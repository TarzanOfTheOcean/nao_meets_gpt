from flask import Flask, request, jsonify
from naoqi import ALProxy, ALModule, ALBroker


app = Flask(__name__)

nao = True
nao_IP = 'nao.local'
port = 9559
broker = "myBroker"

tts = ALProxy("ALTextToSpeech", nao_IP, port)
audio_recorder = ALProxy("ALAudioRecorder", nao_IP, port)

@app.route('/talk', methods=['POST'])
def talk():
    print("Received a request to talk")
    message = request.json.get('message')
    tts.say(str(message))
    return jsonify(success=True)

# NAOqi module for capturing audio
class AudioCaptureModule(ALModule):
    def __init__(self, name):
        ALModule.__init__(self, name)
        self.audio_device = ALProxy("ALAudioDevice", nao_IP, port)
        self.is_listening = False
        self.buffers = []

    def start_listening(self):
        self.audio_device.setClientPreferences(self.getName(), 16000, 3, 0)
        self.audio_device.subscribe(self.getName())
        self.is_listening = True

    def stop_listening(self):
        self.audio_device.unsubscribe(self.getName())
        self.is_listening = False

    def processRemote(self, nbOfChannels, nbOfSamplesByChannel, timeStamp, inputBuffer):
        if self.is_listening:
            self.buffers.append(inputBuffer)

    def get_audio_chunk(self):
        if self.buffers:
            return self.buffers.pop(0)
        return None

# Set up broker connection
try:
    pythonBroker = ALBroker("pythonBroker", "0.0.0.0", 0, nao_IP, port)
    global AudioCapture
    AudioCapture = AudioCaptureModule("AudioCapture")
except RuntimeError:
    print("Error initializing broker!")
    exit(1)


@app.route('/start_listening', methods=['POST'])
def start_listening():
    print("Received a request to start listening")
    AudioCapture.start_listening()
    return jsonify(success=True)

@app.route('/stop_listening', methods=['POST'])
def stop_listening():
    print("Received a request to stop listening")
    AudioCapture.stop_listening()
    return jsonify(success=True)

@app.route('/get_audio_chunk', methods=['GET'])
def get_audio_chunk():
    print("Received a request to get an audio chunk")
    audio_data = AudioCapture.get_audio_chunk()
    if audio_data:
        return audio_data  # Send the audio data as a response
    while not audio_data: # Wait until audio data is available
        audio_data = AudioCapture.get_audio_chunk()
    return audio_data

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5004)