import os
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

def get_max_num_iterations(desired_num_iterations=5):
    max_num_iterations = 25 # the more iterations, the more accurate the results, but slower & pricey
    if os.getenv('LLM_TYPE') == "ollama":
        max_num_iterations = 3
    if desired_num_iterations > max_num_iterations:
        return max_num_iterations
    return desired_num_iterations

def get_llm(openai="gpt-4",ollama="phi3:3.8b-mini-128k-instruct-q8_0", temperature=0):
    if os.getenv('LLM_TYPE') == "ollama":
        base_url = os.getenv('OPENAI_API_BASE') or "http://localhost:11434"
        #return Ollama(model=ollama, temperature=temperature, num_predict=-1, base_url=base_url)
        return ChatOpenAI(
            api_key="ollama",
            base_url=f"{base_url}/v1",
            temperature=0,
            model = ollama)
    else:
        return ChatOpenAI(model = openai, temperature=temperature)
    
# to lower costs, we should use Ollama for the least important tasks, such as adaptToStyle
def get_ollama_model(model="phi3:3.8b-mini-128k-instruct-q8_0",temperature=0):
    base_url = "http://localhost:11434"
    return ChatOpenAI(
            api_key="ollama",
            base_url=f"{base_url}/v1",
            temperature=temperature,
            model = model)

def query_ollama(model="phi3:3.8b-mini-128k-instruct-q8_0",temperature=0,prompt=""):
    llm = get_ollama_model(model,temperature)
    template = """Question: {question}

    Answer: Let's think step by step."""

    prompt = PromptTemplate.from_template(template)
    llm_chain = prompt | llm
    return llm_chain.invoke({ "question": prompt }) 