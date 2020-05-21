from flask import Flask, Response,render_template
import pyaudio

app = Flask(__name__)


FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 16000
CHUNK = 4096
DEV_INDEX = 2

audio1 = pyaudio.PyAudio()

# print out available mic devices
for ii in range(audio1.get_device_count()):
    print(audio1.get_device_info_by_index(ii).get('name'))

def genHeader(sampleRate, bitsPerSample, channels):
    datasize = 2000*10**6
    o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                              # (4byte) File type
    o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
    o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
    return o

@app.route('/audio')
def audio():

    # generate header just once
    sampleRate = RATE
    bitsPerSample = 16
    channels = CHANNELS
    wav_header = genHeader(sampleRate, bitsPerSample, channels)

    stream = audio1.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True, input_device_index=DEV_INDEX,
                    frames_per_buffer=CHUNK)

    # start Recording
    def sound():
        #frames = []
        first_run = True
        while True:
           if first_run:
               data = wav_header + stream.read(CHUNK)
               first_run = False
           else:
               data = stream.read(CHUNK)
           yield(data)

    return Response(sound())

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('mictest.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, threaded=True,port=5000)
