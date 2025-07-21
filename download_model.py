from sentence_transformers import SentenceTransformer

# Download and save the model
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('exported_model')  # Creates a folder in the same directory
print("✅ Model saved to 'exported_model'")
