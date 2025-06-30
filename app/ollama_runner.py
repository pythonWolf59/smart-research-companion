from gpt4all import GPT4All

# Initialize model once globally
model = GPT4All("phi-3-mini.bin")  # path to your local quantized model file

def call_phi(prompt):
    response = model.generate(prompt)
    return response
