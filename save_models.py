import os
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Define the paths to save the model and tokenizer
model_path = os.path.join("saved_models", "model")
tokenizer_path = os.path.join("saved_models", "tokenizer")

# Download the model and tokenizer
model = AutoModelForSequenceClassification.from_pretrained("textattack/bert-base-uncased-qqp")
tokenizer = AutoTokenizer.from_pretrained("textattack/bert-base-uncased-qqp")

# Save the model and tokenizer to files
model.save_pretrained(model_path)
tokenizer.save_pretrained(tokenizer_path)

print("Models and tokenizers saved successfully.")
