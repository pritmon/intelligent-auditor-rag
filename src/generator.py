import yaml
import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (like API keys) from the .env file
load_dotenv()

# The Generator class handles talking to the LLM (like GPT-4) and getting the final answer
class Generator:
    def __init__(self, prompt_path: str = "prompts/system_prompt.yaml"):
        """
        Initializes the Generator.
        
        :param prompt_path: Path to the YAML file containing our "Intelligent Auditor" rules.
        """
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Load the prompt rules from the YAML file
        with open(prompt_path, 'r') as f:
            prompt_data = yaml.safe_load(f)
            self.system_prompt_template = prompt_data.get('system_prompt', "")

    def generate_response(self, query: str, context_chunks: List):
        """
        Constructs the final prompt and asks the LLM for a response.
        """
        print("--- Generating final response from LLM ---")
        
        # 1. Prepare the context text by joining the chunks and including their metadata
        context_items = []
        for node in context_chunks:
            # Extract metadata (LlamaIndex stores page info here)
            file_name = node.metadata.get('file_name', 'Unknown File')
            page_label = node.metadata.get('page_label', 'Unknown Page')
            
            # Combine the metadata with the text so the LLM knows the source
            chunk_content = f"--- [FILE: {file_name}, PAGE: {page_label}] ---\n{node.text}"
            context_items.append(chunk_content)
            
        context_str = "\n\n".join(context_items)
        
        # 2. Fill in the placeholders in our template
        # {context_str} and {query_str} are replaced with the actual text
        full_prompt = self.system_prompt_template.format(
            context_str=context_str,
            query_str=query)
        
        # 3. Call the OpenAI API
        # We send the prompt as a 'user' message with instructions built-in
        response = self.client.chat.completions.create(
            model="gpt-4o-mini", # Using gpt-4o-mini for efficient auditing
            messages=[
                {"role": "system", "content": "You are a precise financial auditor."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.0 # Temperature 0 ensures the AI is consistent and doesn't "hallucinate"
        )
        
        return response.choices[0].message.content

if __name__ == "__main__":
    print("Generator class ready. Make sure OPENAI_API_KEY is in your .env file.")
