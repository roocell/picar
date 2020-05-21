import alsaaudio
import numpy as np
import array
import wave

# constants
CHANNELS    = 2
INFORMAT    = alsaaudio.PCM_FORMAT_S16_LE
RATE        = 16000
FRAMESIZE   = 1024
RECORD_SECONDS = 3
wav_output_filename = 'test1.wav' # name of .wav file

# set up audio input
recorder=alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK,device='hw:1,0')
recorder.setchannels(CHANNELS)
recorder.setrate(RATE)
recorder.setformat(INFORMAT)
recorder.setperiodsize(FRAMESIZE)


buffer = array.array('f')
for i in range(0, int(RATE / FRAMESIZE * RECORD_SECONDS)):
    buffer.fromstring(recorder.read()[1])
data = np.array(buffer, dtype='b')

#frames = []
#for ii in range(0,int((RATE/FRAMESIZE)*RECORD_SECONDS)):
#    data = recorder.read()[1]
#    frames.append(data)

# save the audio frames as .wav file
wavefile = wave.open(wav_output_filename,'wb')
wavefile.setnchannels(CHANNELS)
wavefile.setsampwidth(2)
wavefile.setframerate(RATE)
wavefile.writeframes(data)
wavefile.close()
