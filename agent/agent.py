import os
import pandas as pd
import ollama
import json
from dotenv import load_dotenv
import re

load_dotenv()

# --- Data Loading ---
try:
    df = pd.read_csv("AUTALIC.csv")
except FileNotFoundError:
    print("Warning: AUTALIC.csv not found. Tool to get examples will not work.")
    df = pd.DataFrame()

try:
    with open("data/autalic_paper.txt", "r") as f:
        AUTALIC_PAPER_CONTENT = f.read()
except FileNotFoundError:
    print("Warning: data/autalic_paper.txt not found. Tool to search the paper will not work.")
    AUTALIC_PAPER_CONTENT = ""

# --- Tool Definitions ---

def get_sentence_examples(category: str, num_examples: int = 3):
    """
    Retrieves example sentences from the AUTALIC dataset. Use this to get examples
    of anti-autistic or not-anti-autistic language to help inform an analysis.
    """
    if df.empty:
        return "Dataset not loaded. Cannot provide examples."
    if category == "anti-autistic":
        filtered_df = df[(df[['A1', 'A2', 'A3']] == 1).sum(axis=1) >= 2]
    elif category == "not-anti-autistic":
        filtered_df = df[(df[['A1', 'A2', 'A3']] == 0).sum(axis=1) >= 2]
    else:
        return f"Invalid category: {category}. Please use 'anti-autistic' or 'not-anti-autistic'."
    if filtered_df.empty:
        return f"No examples found for category: {category}"
    return filtered_df['sentence'].sample(n=min(num_examples, len(filtered_df))).tolist()

def search_autalic_paper(query: str):
    """
    Searches the content of the AUTALIC paper summary for a given query. Use this
    to answer questions about the AUTALIC paper, its findings, or its methodology.
    """
    if not AUTALIC_PAPER_CONTENT:
        return "Paper content not loaded. Cannot search."
    
    results = []
    for line in AUTALIC_PAPER_CONTENT.splitlines():
        if re.search(query, line, re.IGNORECASE):
            results.append(line)
            
    if not results:
        return f"No information found for '{query}'. Try a broader search term."
        
    return "\n".join(results)

# --- Agent Class ---

class AutalicAgent:
    def __init__(self):
        self.client = ollama.Client()
        self.model = "qwen3:14b" # Using the new, tool-supporting model
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_sentence_examples",
                    "description": "Get example sentences from the AUTALIC dataset to inform an analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "enum": ["anti-autistic", "not-anti-autistic"]},
                            "num_examples": {"type": "integer", "default": 3}
                        },
                        "required": ["category"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_autalic_paper",
                    "description": "Searches the AUTALIC paper summary to answer questions about the research.",
                    "parameters": {
                        "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]
                    },
                },
            }
        ]

    def run(self, history):
        system_prompt = {
            "role": "system",
            "content": (
                "You are the AUTALIC Agent, a friendly and helpful conversational AI created by Naba Rizvi. "
                "Your primary roles are: \n"
                "1.  To analyze sentences for anti-autistic ableism. \n"
                "2.  To answer questions about the AUTALIC research paper. \n"
                "3.  To engage in friendly, general conversation. \n\n"
                "When a user provides a sentence for analysis, you MUST use your tools if needed and then respond with a single, valid JSON object containing 'classification' and 'confidence' keys. Do not add any conversational text to the JSON response. \n"
                "When a user asks a question about the AUTALIC paper, you MUST use the `search_autalic_paper` tool to find the relevant information and then answer in a clear, conversational, and helpful manner. \n"
                "For all other interactions (greetings, general chat), just be a friendly conversationalist. Do not try to analyze these messages or use tools unless explicitly asked."
            ),
        }
        messages = [system_prompt] + history

        for _ in range(5):
            response = self.client.chat(model=self.model, messages=messages, tools=self.tools)
            response_message = response['message']
            messages.append(response_message)

            if response_message.get('tool_calls'):
                available_tools = {"get_sentence_examples": get_sentence_examples, "search_autalic_paper": search_autalic_paper}
                for tool_call in response_message['tool_calls']:
                    function_name = tool_call['function']['name']
                    tool_to_call = available_tools.get(function_name)
                    if tool_to_call:
                        tool_response = tool_to_call(**tool_call['function']['arguments'])
                        messages.append({"role": "tool", "content": str(tool_response), "name": function_name, "tool_call_id": tool_call['id']})
            else:
                return response_message['content']
        
        return "I seem to be having trouble using my tools right now. Please try again."

if __name__ == '__main__':
    agent = AutalicAgent()
    print("\n--- Paper Question Example ---")
    result = agent.run([{"role": "user", "content": "What did the AUTALIC paper find about LLMs?"}])
    print(result) 