import os
import certifi
import whisper

os.environ['SSL_CERT_FILE'] = certifi.where()

whisper_model = whisper.load_model('base')
