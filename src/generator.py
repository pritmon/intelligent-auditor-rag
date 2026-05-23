import yaml
import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class Generator:
    def __init__(self, prompt_path: str = "prompts/system_prompt.yaml"):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        self.client = OpenAI(api_key=api_key)

        # ── HIGH-8: read model from env so it stays in sync with Settings.llm ──
        self.model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

        # ── MED-4: explicit, actionable errors for missing / malformed prompt file ──
        try:
            with open(prompt_path, 'r') as f:
                prompt_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"System prompt file not found: {prompt_path!r}")
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in prompt file {prompt_path!r}: {exc}")

        self.system_prompt_template = prompt_data.get('system_prompt')
        if not self.system_prompt_template:
            raise ValueError(f"'system_prompt' key missing or empty in {prompt_path!r}")

    def generate_response(self, query: str, context_chunks: List) -> str:
        context_items = []
        for node in context_chunks:
            file_name = node.metadata.get('file_name', 'Unknown File')
            page_label = node.metadata.get('page_label', 'Unknown Page')
            chunk_content = f"--- [FILE: {file_name}, PAGE: {page_label}] ---\n{node.text}"
            context_items.append(chunk_content)

        context_str = "\n\n".join(context_items)

        # ── CRIT-3: use plain string replacement instead of .format() so that
        #    curly braces inside user query or retrieved document text cannot
        #    trigger KeyError / template manipulation. ──
        full_prompt = (
            self.system_prompt_template
            .replace("{context_str}", context_str)
            .replace("{query_str}", query)
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a precise financial auditor."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.0
        )

        return response.choices[0].message.content


if __name__ == "__main__":
    print("Generator class ready. Make sure OPENAI_API_KEY is in your .env file.")
