from gpt4all import GPT4All

model = None

def ensure_model_ready():
    global model
    if model is None:
        model = GPT4All("path/to/phi-3-mini-quantized.bin")
        print("Model loaded successfully")
    return model
