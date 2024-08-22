import os
import certifi
import whisper

# Force urllib to use certifi's certificate bundle
os.environ['SSL_CERT_FILE'] = certifi.where()

# Load the model
whisper_model = whisper.load_model('base')
