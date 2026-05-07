import time
import json
from google import genai
from google.genai import types
import anthropic
from config import GEMINI_API_KEY, ANTHROPIC_API_KEY, GEMINI_MODEL, ANTHROPIC_MODEL
from utils import search_web, search_wikipedia, save_to_txt, save_to_md

current_date = time.strftime("%Y-%m-%d")

SYSTEM_PROMPT = """You are a research assistant. 
When asked to research a topic:
1. Use the search_web and search_wikipedia tools to gather information.
2. Summarize findings in a clear and structured way and add citations for any information retrieved from the tools.
3. For instance, if you find information about "X is the capital of Y" from a web search, you should include a citation 
like [1] in the summary and then list the source at the end of the summary as [1] Source: URL.
4. If asked to save the results, use the save_to_txt or save_to_md tool IMMEDIATELY without asking the user again.
5. NEVER ask the user if they want to save - this has already been decided upfront.
6. Today is {current_date} - make sure to use the most recent information available from the tools, especially for current events or rapidly changing topics.
""".format(current_date=current_date)

# --- Setup clients ---
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# --- Define tools for Gemini ---
gemini_tools = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="search_web",
        description="Search the web using DuckDuckGo for recent information.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "query": types.Schema(type=types.Type.STRING, description="The search query"),
            },
            required=["query"],
        ),
    ),
    types.FunctionDeclaration(
        name="search_wikipedia",
        description="Search Wikipedia for background information on a topic.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "query": types.Schema(type=types.Type.STRING, description="The topic to search on Wikipedia"),
            },
            required=["query"],
        ),
    ),
    types.FunctionDeclaration(
        name="save_to_txt",
        description="Save the research output to a TXT file.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "content": types.Schema(type=types.Type.STRING, description="The content to save"),
                "filename": types.Schema(type=types.Type.STRING, description="The filename without extension"),
            },
            required=["content", "filename"],
        ),
    ),
    types.FunctionDeclaration(
        name="save_to_md",
        description="Save the research output to a Markdown (.md) file.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "content": types.Schema(type=types.Type.STRING, description="The content to save"),
                "filename": types.Schema(type=types.Type.STRING, description="The filename without extension"),
            },
            required=["content", "filename"],
        ),
    ),
])

# --- Define tools for Anthropic ---
anthropic_tools = [
    {
        "name": "search_web",
        "description": "Search the web using DuckDuckGo for recent information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_wikipedia",
        "description": "Search Wikipedia for background information on a topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The topic to search on Wikipedia"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "save_to_txt",
        "description": "Save the research output to a TXT file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The content to save"},
                "filename": {"type": "string", "description": "The filename without extension"},
            },
            "required": ["content", "filename"],
        },
    },
    {
        "name": "save_to_md",
        "description": "Save the research output to a Markdown (.md) file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The content to save"},
                "filename": {"type": "string", "description": "The filename without extension"},
            },
            "required": ["content", "filename"],
        },
    },
]

# --- Tool dispatcher ---
def dispatch_tool(name: str, args: dict) -> str:
    if name == "search_web":
        return search_web(**args)
    elif name == "search_wikipedia":
        return search_wikipedia(**args)
    elif name == "save_to_txt":
        return save_to_txt(**args)
    elif name == "save_to_md":
        return save_to_md(**args)
    else:
        return f"Unknown tool: {name}"

# --- Gemini agentic loop ---
def run_gemini(user_prompt: str):
    def call_with_retry(messages, max_retries=3):
        for attempt in range(max_retries):
            try:
                return gemini_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=messages,
                    config=types.GenerateContentConfig(
                        tools=[gemini_tools],
                        system_instruction=SYSTEM_PROMPT  # added
                    )
                )
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    wait_time = (attempt + 1) * 10
                    print(f"⚠️ Gemini is busy. Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    raise e
        print("❌ Gemini is unavailable after multiple retries. Please try again later.")
        return None

    messages = [types.Content(role="user", parts=[types.Part(text=user_prompt)])]

    while True:
        response = call_with_retry(messages)
        if response is None:
            break

        candidate = response.candidates[0]
        messages.append(types.Content(role="model", parts=candidate.content.parts))

        tool_calls = [p for p in candidate.content.parts if p.function_call]

        if not tool_calls:
            final_text = "".join(p.text for p in candidate.content.parts if p.text)
            print("📋 Research Results:\n")
            print(final_text)
            break

        tool_results = []
        for part in tool_calls:
            fn_name = part.function_call.name
            fn_args = dict(part.function_call.args)
            print(f"🔧 Using tool: {fn_name} for {fn_args}")
            result = dispatch_tool(fn_name, fn_args)
            print(f"✅ Tool result: {result}")
            tool_results.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fn_name,
                        response={"result": result}
                    )
                )
            )

        messages.append(types.Content(role="user", parts=tool_results))

# --- Anthropic agentic loop ---
def run_anthropic(user_prompt: str):
    messages = [{"role": "user", "content": user_prompt}]

    while True:
        response = anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            tools=anthropic_tools,
            system=SYSTEM_PROMPT,  # added
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        # Check if there are tool calls
        tool_calls = [b for b in response.content if b.type == "tool_use"]

        if not tool_calls:
            # No more tool calls - print final response
            final_text = "".join(b.text for b in response.content if hasattr(b, "text"))
            print("📋 Research Results:\n")
            print(final_text)
            break

        # Execute tool calls
        tool_results = []
        for tool_call in tool_calls:
            fn_name = tool_call.name
            fn_args = tool_call.input
            print(f"🔧 Using tool: {fn_name} for {fn_args}")
            result = dispatch_tool(fn_name, fn_args)
            print(f"✅ Tool result: {result}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": result,
            })

        messages.append({"role": "user", "content": tool_results})

# --- Ask user for input ---
print("\n🔍 Research Assistant\n")
llm_choice = input("Which LLM do you want to use? (gemini/claude): ").strip().lower()
topic = input("What topic do you want to research? ")
save_option = input("Do you want to save the results? (yes/no): ").strip().lower()

if save_option == "yes":
    save_format = input("Save as TXT or MD? (txt/md): ").strip().lower()
    filename = input("Enter filename (without extension): ").strip()
    user_prompt = (
        f"Research the following topic thoroughly using web search and Wikipedia: '{topic}'. "
        f"Summarize the findings in a clear and structured way. "
        f"Then save the results to a {save_format} file named '{filename}'."
    )
else:
    user_prompt = (
        f"Research the following topic thoroughly using web search and Wikipedia: '{topic}'. "
        f"Summarize the findings in a clear and structured way and print the results."
    )

print("\n⏳ Researching...\n")

if llm_choice == "claude":
    print("🤖 Using Anthropic Claude\n")
    run_anthropic(user_prompt)
else:
    print("🤖 Using Google Gemini\n")
    run_gemini(user_prompt)