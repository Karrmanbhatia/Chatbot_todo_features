import os
import yaml
import re

def main():
    # First, locate the nlu.yml file
    nlu_file = 'nlu.yml'
    if not os.path.exists(nlu_file):
        print(f"Could not find {nlu_file} in current directory: {os.getcwd()}")
        # Try looking in data directory
        for possible_path in ['data/nlu.yml', 'data/nlu/nlu.yml']:
            if os.path.exists(possible_path):
                nlu_file = possible_path
                print(f"Found NLU file at: {nlu_file}")
                break
    
    if not os.path.exists(nlu_file):
        print("Could not find nlu.yml file. Please specify the correct path.")
        return
        
    print(f"Reading NLU data from: {nlu_file}")
    
    # Load the YAML file
    try:
        with open(nlu_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"File content length: {len(content)} characters")
            
            # Simple check to see if the file has content
            if len(content.strip()) < 10:
                print("File seems to be empty or contains very little content")
                return
                
            # Try to load YAML
            try:
                data = yaml.safe_load(content)
                print(f"Successfully parsed YAML. Structure: {type(data)}")
                
                # Check if the file has the expected structure
                if not isinstance(data, dict) or 'nlu' not in data:
                    print(f"NLU data has unexpected structure: {data.keys() if isinstance(data, dict) else type(data)}")
                    return
                    
                # Print basic stats about the NLU data
                nlu_data = data['nlu']
                print(f"Found {len(nlu_data)} intents")
                
                # Check for entities
                entity_count = 0
                entity_types = set()
                problematic_examples = []
                
                for item in nlu_data:
                    if 'intent' in item and 'examples' in item:
                        intent_name = item['intent']
                        examples = item['examples'].strip().split('\n')
                        
                        for example in examples:
                            # Remove the leading '- ' if it exists
                            if example.startswith('- '):
                                example = example[2:]
                            
                            # Check for entity annotations
                            entities = re.findall(r'\[(.*?)\]\((.*?)\)', example)
                            entity_count += len(entities)
                            
                            for entity_text, entity_type in entities:
                                entity_types.add(entity_type)
                                
                                # Check for potential problems
                                if '[' in entity_text or ']' in entity_text:
                                    problematic_examples.append((intent_name, example, "Nested square brackets"))
                                if '(' in entity_text or ')' in entity_text:
                                    problematic_examples.append((intent_name, example, "Nested parentheses"))
                
                print(f"Found {entity_count} entity annotations of {len(entity_types)} types: {', '.join(entity_types)}")
                
                if problematic_examples:
                    print("\nPotentially problematic examples:")
                    for intent, example, reason in problematic_examples:
                        print(f"- Intent '{intent}': {example} - {reason}")
                else:
                    print("\nNo obvious issues detected in entity annotations.")
                    
            except yaml.YAMLError as e:
                print(f"Error parsing YAML: {e}")
                
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    main()