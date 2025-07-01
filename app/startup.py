from gpt4all import GPT4All

model = None

def ensure_model_ready():
    global model
    model_path = "E:/Models/Llama-3.2-3B-Instruct-Q4_0.gguf"  # ✅ Must be a file, not a directory

    model = GPT4All(model_name=model_path,
                    n_ctx=16684,
                    verbose=True)

    print("✅ Model loaded successfully!")

def get_model():
    return model
