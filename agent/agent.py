import os
import pandas as pd
import ollama
import json
from dotenv import load_dotenv
import re
import logging

# Add the logging configuration at the top of agent.py
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

# --- Data Loading ---
try:
    df = pd.read_csv("AUTALIC.csv")
except FileNotFoundError:
    logging.warning("AUTALIC.csv not found. Tool to get examples will not work.")
    df = pd.DataFrame()

try:
    with open("data/autalic_paper.txt", "r") as f:
        AUTALIC_PAPER_CONTENT = f.read()
except FileNotFoundError:
    logging.warning("data/autalic_paper.txt not found. Tool to search the paper will not work.")
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
        filtered_df = df[(df[['A1_Score', 'A2_Score', 'A3_Score']] == 1).sum(axis=1) >= 2]
    elif category == "not-anti-autistic":
        filtered_df = df[(df[['A1_Score', 'A2_Score', 'A3_Score']] == 0).sum(axis=1) >= 2]
    else:
        return f"Invalid category: {category}. Please use 'anti-autistic' or 'not-anti-autistic'."
    if filtered_df.empty:
        return f"No examples found for category: {category}"
    return filtered_df['Sentence'].sample(n=min(num_examples, len(filtered_df))).tolist()

def search_autalic_paper(query: str):
    """
    Searches the content of the AUTALIC paper summary. If the query is vague 
    (e.g., 'the paper'), it returns the core contribution. Otherwise, it searches 
    for specific information.
    """
    if not AUTALIC_PAPER_CONTENT:
        return "Paper content not loaded. Cannot search."

    # Define vague queries that should return the core contribution by default
    vague_queries = ["paper", "publication", "text", "full-text", "autalic", "the paper"]
    if query.lower().strip() in vague_queries:
        try:
            # Extract the Core Contribution section
            content_lines = AUTALIC_PAPER_CONTENT.splitlines()
            in_section = False
            section_content = []
            for line in content_lines:
                if "### 1. Core Contribution" in line:
                    in_section = True
                    continue
                if in_section and line.startswith("###"):
                    break
                if in_section and line.strip():
                    section_content.append(line)
            if section_content:
                return "\n".join(section_content)
        except Exception:
            # Fallback if parsing fails, just do a normal search
            pass

    # If not a vague query or parsing failed, perform a specific search
    results = []
    for line in AUTALIC_PAPER_CONTENT.splitlines():
        if re.search(query, line, re.IGNORECASE):
            results.append(line)

    if not results:
        # If no results are found, return a markdown link to the website
        return "[The AUTALIC research paper is available here](https://nrizvi.github.io/AUTALIC.html)"

    return "\n".join(results)


# --- Agent Class ---

class AutalicAgent:
    def __init__(self):
        self.client = ollama.Client()
        self.model = "qwen3:14b"
        self.tools = [
            {"type": "function", "function": {"name": "get_sentence_examples", "description": "Get example sentences from the AUTALIC dataset to inform an analysis.", "parameters": {"type": "object", "properties": {"category": {"type": "string", "enum": ["anti-autistic", "not-anti-autistic"]}, "num_examples": {"type": "integer", "default": 3}}, "required": ["category"]}}},
            {"type": "function", "function": {"name": "search_autalic_paper", "description": "Searches the AUTALIC paper summary to answer questions about the research.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}
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
                "When a user provides a sentence for analysis, you MUST first show your reasoning inside <think>...</think> tags. Then, on a new line, provide the analysis in the format: 'I classify this sentence as [classification] with [confidence]% confidence.' Do not output a JSON object for the analysis. \n"
                "When a user asks a question about the AUTALIC paper, you MUST use the `search_autalic_paper` tool to find the relevant information and then answer in a clear, conversational, and helpful manner. \n"
                "For all other interactions (greetings, general chat), just be a friendly conversationalist. Do not try to analyze these messages or use tools unless explicitly asked."
            ),
        }
        messages = [system_prompt] + history

        for i in range(5):
            try:
                logging.info(f"AutalicAgent: Starting chat iteration {i+1}")
                response = self.client.chat(model=self.model, messages=messages, tools=self.tools)
                response_message = response['message']
                messages.append(response_message)
                logging.debug(f"AutalicAgent: Ollama raw response_message: {response_message}")

                if response_message.get('tool_calls'):
                    logging.info("AutalicAgent: Ollama requested tool calls.")
                    available_tools = {"get_sentence_examples": get_sentence_examples, "search_autalic_paper": search_autalic_paper}
                    for tool_call in response_message['tool_calls']:
                        function_name = tool_call['function']['name']
                        tool_args = tool_call['function']['arguments']
                        logging.info(f"AutalicAgent: Attempting to call tool: {function_name} with arguments: {tool_args}")
                        tool_to_call = available_tools.get(function_name)
                        if tool_to_call:
                            try:
                                tool_response = tool_to_call(**tool_args)
                                messages.append({"role": "tool", "content": str(tool_response)})
                                logging.info(f"AutalicAgent: Tool '{function_name}' executed successfully.")
                                logging.debug(f"AutalicAgent: Tool response: {str(tool_response)[:200]}...")
                            except Exception as e:
                                logging.critical(f"AutalicAgent: Error executing tool '{function_name}' with args {tool_args}: {e}", exc_info=True)
                                messages.append({"role": "tool", "content": f"Error: Could not execute tool '{function_name}'. Details: {e}"})
                        else:
                            logging.error(f"AutalicAgent: Tool '{function_name}' not found in available_tools.")
                            messages.append({"role": "tool", "content": f"Error: Tool '{function_name}' not found."})
                else:
                    logging.info("AutalicAgent: Ollama did not request tool calls. Returning final content.")
                    return response_message['content']

            except ollama.ResponseError as e:
                logging.critical(f"AutalicAgent: Ollama API Response Error: Status {e.status_code}, Message: {e.error}", exc_info=True)
                return f"An error occurred with the Ollama server: {e.error} (Status: {e.status_code})"
            except Exception as e:
                logging.critical(f"AutalicAgent: An unexpected error occurred during chat iteration {i+1}: {e}", exc_info=True)
                return "An unexpected internal error occurred in the agent."
        
        logging.warning("AutalicAgent: Agent reached maximum iterations without producing a final response.")
        return "I seem to be having trouble using my tools right now. Please try again."

if __name__ == '__main__':
    # --- Direct Tool Call Example for Debugging ---
    temp_autalic_paper_content = ""
    try:
        with open("data/autalic_paper.txt", "r") as f:
            temp_autalic_paper_content = f.read()
        print("data/autalic_paper.txt loaded successfully for direct test.")
    except FileNotFoundError:
        print("data/autalic_paper.txt not found for direct test.")

    if temp_autalic_paper_content:
        def _temp_search_autalic_paper_test(query: str):
            if not temp_autalic_paper_content:
                return "Paper content not loaded for direct test."
            results = []
            for line in temp_autalic_paper_content.splitlines():
                if re.search(query, line, re.IGNORECASE):
                    results.append(line)
            if not results:
                return f"No information found for '{query}'. Try a broader search term."
            return "\n".join(results)

        print("\n--- Direct search_autalic_paper Tool Call ---")
        direct_tool_output = _temp_search_autalic_paper_test("LLMs")
        print("Direct tool output:")
        print(direct_tool_output)
        print("-" * 30)
    else:
        print("Cannot perform direct tool test as autalic_paper.txt is missing or empty.")

    # Your original agent run
    agent = AutalicAgent()
    print("\n--- Agent Run Example ---")
    result = agent.run([{"role": "user", "content": "What did the AUTALIC paper find about LLMs?"}])
    print(f"Agent final response: {result}") 