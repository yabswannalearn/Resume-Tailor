"""
Agent Core for Resume Tailor.

PURPOSE:
This is the "brain" of the agent. Instead of running a fixed pipeline,
the agent receives a natural language goal from the user and DECIDES
what to do on its own using a ReAct loop:

    THINK → ACT → OBSERVE → THINK → ACT → OBSERVE → ... → FINAL ANSWER

HOW IT WORKS (step by step):

1. We build a SYSTEM PROMPT that tells Gemini:
   - "You are an AI agent with access to these tools: [list]"
   - "You must respond in a specific JSON format"
   - "Either call a tool OR give a final answer"

2. We inject MEMORY (past sessions) into the prompt so the agent
   has context from previous interactions.

3. We start a LOOP (max 10 iterations for safety):
   a. Send the full conversation history to Gemini
   b. Gemini responds with either:
      - A TOOL CALL: {"action": "tool_name", "args": {...}, "thought": "why I'm doing this"}
      - A FINAL ANSWER: {"action": "final_answer", "summary": "...", "thought": "..."}
   c. If tool call → we execute the tool, add the result to history, loop again
   d. If final answer → we break out of the loop and return

4. A shared STATE dict is passed to every tool so they can store/read
   data from each other (e.g., analyze_job stores job_data, build_resume reads it).

5. All steps are logged so we can return a full trace of the agent's reasoning.
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from modules.tools import get_tool_descriptions, get_tool_by_name
from modules.memory import format_memory_for_prompt, save_session

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(os.getenv("GEMINI_MODEL"))

# Maximum number of reasoning steps before the agent is forced to stop.
# This prevents infinite loops if Gemini keeps calling tools endlessly.
MAX_ITERATIONS = 10


def build_system_prompt() -> str:
    """
    Build the system prompt that tells Gemini HOW to be an agent.
    This is the most critical piece — it defines the agent's behavior.
    """

    tool_descriptions = get_tool_descriptions()
    memory_context = format_memory_for_prompt()

    return f"""You are an AI Resume Tailor Agent. You help users create tailored resumes, review their CVs, and research companies — all through natural language.

You have access to the following tools:

{tool_descriptions}

## HOW TO RESPOND

You MUST respond with ONLY a valid JSON object in one of these two formats:

### Format 1: Call a tool
{{
    "action": "<tool_name>",
    "args": {{ <tool arguments if any> }},
    "thought": "explain WHY you are calling this tool"
}}

### Format 2: Give your final answer (when you're done)
{{
    "action": "final_answer",
    "thought": "explain why you are done",
    "summary": "a clear summary of everything you did and the results"
}}

## RULES
1. Call ONE tool at a time. After each tool call, you'll see the result and can decide your next move.
2. Think step-by-step. Always explain your reasoning in the "thought" field.
3. If a tool returns an error, adapt — try a different approach or inform the user.
4. When you have completed the user's goal, use "final_answer" to stop.
5. Do NOT invent tools that don't exist. Only use the tools listed above.
6. The "args" field should only include parameters listed in the tool description. For tools with no parameters, use an empty object {{}}.
7. Output ONLY the JSON object, nothing else. No markdown, no extra text.

## MEMORY (past sessions)
{memory_context}
"""


def parse_agent_response(raw_text: str) -> dict:
    """
    Parse Gemini's response into a structured dict.
    Handles the common case where Gemini wraps JSON in markdown code fences.
    """
    text = raw_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    return json.loads(text)


def run(goal: str) -> dict:
    """
    Main agent entry point.

    Takes a natural language goal from the user and runs the ReAct loop
    until the agent decides it's done or hits the iteration limit.

    Returns a dict with:
        - steps: list of all reasoning steps (thought + action + result)
        - final_summary: the agent's final answer
        - state: the shared state bag (contains job_data, resume, etc.)
        - pdf_path: path to the generated PDF if one was created
    """

    # The system prompt defines the agent's identity and tools
    system_prompt = build_system_prompt()

    # Conversation history — this grows as the agent calls tools
    # The agent sees this full history on every iteration
    conversation = [
        {"role": "user", "parts": [f"My goal: {goal}"]},
    ]

    # Shared state bag — tools read/write data here
    # e.g., analyze_job writes state["job_data"], build_resume reads it
    state = {}

    # Log of all reasoning steps for transparency
    steps = []

    # Track which tools were called (for memory)
    tools_used = []

    for iteration in range(MAX_ITERATIONS):
        # ── THINK: Send everything to Gemini and ask what to do ──
        response = model.generate_content(
            [{"role": "user", "parts": [system_prompt]}] + conversation
        )

        raw_response = response.text.strip()

        # ── Parse the response ──
        try:
            decision = parse_agent_response(raw_response)
        except (json.JSONDecodeError, IndexError):
            # If Gemini returns garbage, record it and try once more
            steps.append({
                "iteration": iteration + 1,
                "thought": "Failed to parse response",
                "raw_response": raw_response,
                "action": "parse_error",
            })
            conversation.append({"role": "model", "parts": [raw_response]})
            conversation.append({"role": "user", "parts": [
                "Your response was not valid JSON. Please respond with ONLY a JSON object as specified in the instructions."
            ]})
            continue

        thought = decision.get("thought", "")
        action = decision.get("action", "")

        # ── FINAL ANSWER: The agent is done ──
        if action == "final_answer":
            summary = decision.get("summary", "Task completed.")
            steps.append({
                "iteration": iteration + 1,
                "thought": thought,
                "action": "final_answer",
                "summary": summary,
            })

            # Save this session to memory for future context
            save_session(goal, tools_used, summary)

            return {
                "steps": steps,
                "final_summary": summary,
                "state": _sanitize_state(state),
                "pdf_path": state.get("pdf_path"),
            }

        # ── ACT: Call the requested tool ──
        tool = get_tool_by_name(action)
        if not tool:
            # Agent tried to call a tool that doesn't exist
            error_msg = f"Tool '{action}' does not exist. Available tools: {', '.join(t['name'] for t in __import__('modules.tools', fromlist=['TOOLS']).TOOLS)}"
            steps.append({
                "iteration": iteration + 1,
                "thought": thought,
                "action": action,
                "result": {"status": "error", "message": error_msg},
            })
            conversation.append({"role": "model", "parts": [raw_response]})
            conversation.append({"role": "user", "parts": [f"Tool result: {error_msg}"]})
            continue

        # Execute the tool
        try:
            args = decision.get("args", {})
            result = tool["function"](state, args)
        except Exception as e:
            result = {"status": "error", "message": str(e)}

        tools_used.append(action)

        # ── OBSERVE: Record what happened ──
        step_record = {
            "iteration": iteration + 1,
            "thought": thought,
            "action": action,
            "result": result,
        }
        steps.append(step_record)

        # Add this exchange to the conversation so the agent sees
        # what happened and can decide the next step
        conversation.append({"role": "model", "parts": [raw_response]})
        conversation.append({"role": "user", "parts": [
            f"Tool '{action}' returned:\n{json.dumps(result, indent=2, default=str)}"
        ]})

    # If we hit the iteration limit, force a stop
    save_session(goal, tools_used, "Agent reached maximum iterations without completing.")

    return {
        "steps": steps,
        "final_summary": "I reached the maximum number of reasoning steps. Here's what I accomplished so far.",
        "state": _sanitize_state(state),
        "pdf_path": state.get("pdf_path"),
    }


def _sanitize_state(state: dict) -> dict:
    """
    Clean up the state for the API response.
    Remove very large fields (like full PDF text) to keep the response manageable.
    """
    clean = {}
    for key, value in state.items():
        if key == "identity":
            # Don't dump the entire identity (it has the full PDF text)
            clean[key] = {"loaded": True, "name": value.get("personal", {}).get("name", "Unknown")}
        elif key == "tailored_resume":
            # Include resume but truncate if huge
            clean[key] = {k: v for k, v in value.items() if k != "company_research"}
        else:
            clean[key] = value
    return clean
