import os
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Define the paths to save the model and tokenizer
model_path = os.path.join("saved_models", "model")
tokenizer_path = os.path.join("saved_models", "tokenizer")


model_name = "microsoft/deberta-base-mnli"
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Save the model and tokenizer to files
model.save_pretrained(model_path)
tokenizer.save_pretrained(tokenizer_path)

print("Models and tokenizers saved successfully.")
