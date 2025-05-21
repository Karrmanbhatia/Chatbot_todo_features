# This file shows how to integrate your GPT-Neo model with the TFIA chatbot
# Replace the mock implementation in actions.py with this code when you're ready

import torch
from transformers import GPTNeoForCausalLM, GPT2Tokenizer
import json
import re

class GPTNeoPredictor:
    def __init__(self, model_path=None):
        """
        Initialize the GPT-Neo model for test failure analysis.
        
        Args:
            model_path: Path to your fine-tuned GPT-Neo model
        """
        # If no model path is provided, use a pre-trained model (for demonstration)
        if model_path is None:
            model_name = "EleutherAI/gpt-neo-1.3B"  # You can use different sizes based on your needs
        else:
            model_name = model_path
            
        print(f"Loading GPT-Neo model from {model_name}...")
        
        # Load the model and tokenizer
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        self.model = GPTNeoForCausalLM.from_pretrained(model_name)
        
        # Move to GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        print(f"Model loaded successfully. Using device: {self.device}")
    
    def prepare_input(self, test_data):
        """
        Format the test data as a prompt for GPT-Neo.
        
        Args:
            test_data: Dictionary containing test information
            
        Returns:
            Formatted prompt string
        """
        # Concatenate logs into a single string
        logs = "\n".join(test_data.get("logs", []))
        
        # Create a prompt for GPT-Neo
        prompt = f"""
Test ID: {test_data.get('test_id', 'Unknown')}
Test Title: {test_data.get('title', 'Unknown')}
Description: {test_data.get('description', 'Unknown')}
Error: {test_data.get('error', 'Unknown')}

Logs:
{logs}

Analyze the test failure above and provide:
1. Likely cause of the failure:
2. Confidence level (0-100):
3. Suggested actions to fix:
4. Similar previous cases:
"""
        return prompt
    
    def predict(self, test_data, max_length=300, temperature=0.7):
        """
        Generate a prediction for the test failure.
        
        Args:
            test_data: Dictionary containing test information
            max_length: Maximum length of generated text
            temperature: Controls randomness (lower = more deterministic)
            
        Returns:
            Dictionary with prediction results
        """
        # Prepare the input prompt
        prompt = self.prepare_input(test_data)
        
        # Tokenize the input
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Generate the output
        with torch.no_grad():
            output = self.model.generate(
                inputs.input_ids,
                max_length=len(inputs.input_ids[0]) + max_length,
                temperature=temperature,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode the output
        generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract the response (remove the prompt part)
        response = generated_text[len(prompt):]
        
        # Parse the response to extract structured information
        return self.parse_prediction(response)
    
    def parse_prediction(self, response):
        """
        Parse the GPT-Neo response into structured data.
        
        Args:
            response: Raw text response from GPT-Neo
            
        Returns:
            Dictionary with parsed prediction
        """
        # Initialize default values
        prediction = {
            "cause": "Unknown",
            "confidence": 0,
            "suggestion": "No suggestion available",
            "similar_cases": []
        }
        
        # Extract cause
        cause_match = re.search(r"1\.\s*Likely cause.*?:(.*?)(?=2\.|$)", response, re.DOTALL)
        if cause_match:
            prediction["cause"] = cause_match.group(1).strip()
        
        # Extract confidence
        confidence_match = re.search(r"2\.\s*Confidence level.*?:.*?(\d+)", response, re.DOTALL)
        if confidence_match:
            try:
                prediction["confidence"] = int(confidence_match.group(1))
            except ValueError:
                pass
        
        # Extract suggestion
        suggestion_match = re.search(r"3\.\s*Suggested actions.*?:(.*?)(?=4\.|$)", response, re.DOTALL)
        if suggestion_match:
            prediction["suggestion"] = suggestion_match.group(1).strip()
        
        # Extract similar cases
        cases_match = re.search(r"4\.\s*Similar previous cases.*?:(.*?)(?=$)", response, re.