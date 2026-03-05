"""
Agent Core for Resume Tailor.

PURPOSE:
This is the "brain" of the agent. Instead of running a fixed pipeline,
the agent receives a natural language goal from the user and DECIDES
what to do on its own using a ReAct loop:

    THINK → ACT → OBSERVE → THINK → ACT → OBSERVE → ... → FINAL ANSWER

HOW IT WORKS (step by step):

1. We build a SYSTEM PROMPT that tells the AI:
   - "You are an AI agent with access to these tools: [list]"
   - "You must respond in a specific JSON format"
   - "Either call a tool OR give a final answer"

2. We inject MEMORY (past sessions) into the prompt so the agent
   has context from previous interactions.

3. We start a LOOP (max 10 iterations for safety):
   a. Send the full conversation history to the AI
   b. AI responds with either:
      - A TOOL CALL: {"action": "tool_name", "args": {...}, "thought": "why"}
      - A FINAL ANSWER: {"action": "final_answer", "summary": "...", "thought": "..."}
   c. If tool call → we execute the tool, add the result to history, loop again
   d. If final answer → we break out of the loop and return

4. A shared STATE dict is passed to every tool so they can store/read
   data from each other (e.g., analyze_job stores job_data, build_resume reads it).

5. All steps are logged so we can return a full trace of the agent's reasoning.

UPDATED: Now uses ai_provider.generate() instead of direct Gemini calls.
Works with both Ollama (local Qwen3) and Gemini (cloud).
"""

import json
from modules.ai_provider import generate
from modules.tools import get_tool_descriptions, get_tool_by_name, TOOLS
from modules.memory import format_memory_for_prompt, save_session

# Maximum number of reasoning steps before the agent is forced to stop.
MAX_ITERATIONS = 10


def build_system_prompt() -> str:
    """
    Build the system prompt that tells the AI HOW to be an agent.
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
    Parse the AI's response into a structured dict.
    Handles markdown code fences and other formatting quirks.
    """
    text = raw_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    # Try to find JSON object in the text if it's wrapped in other content
    if not text.startswith("{"):
        start = text.find("{")
        if start != -1:
            # Find the matching closing brace
            depth = 0
            for i in range(start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        text = text[start:i+1]
                        break

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

    # Conversation history — grows as the agent calls tools
    messages = [system_prompt, f"\nMy goal: {goal}\n"]

    # Shared state bag — tools read/write data here
    state = {}

    # Log of all reasoning steps for transparency
    steps = []

    # Track which tools were called (for memory)
    tools_used = []

    for iteration in range(MAX_ITERATIONS):
        # ── THINK: Send everything to the AI and ask what to do ──
        full_prompt = "\n".join(messages)
        raw_response = generate(full_prompt)

        # ── Parse the response ──
        try:
            decision = parse_agent_response(raw_response)
        except (json.JSONDecodeError, IndexError, ValueError):
            # If AI returns garbage, record it and try once more
            steps.append({
                "iteration": iteration + 1,
                "thought": "Failed to parse response",
                "raw_response": raw_response[:500],
                "action": "parse_error",
            })
            messages.append(f"\nAssistant: {raw_response}\n")
            messages.append(
                "\nYour response was not valid JSON. Please respond with ONLY a JSON object "
                "as specified in the instructions. No markdown, no extra text.\n"
            )
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
            available = ", ".join(t["name"] for t in TOOLS)
            error_msg = f"Tool '{action}' does not exist. Available tools: {available}"
            steps.append({
                "iteration": iteration + 1,
                "thought": thought,
                "action": action,
                "result": {"status": "error", "message": error_msg},
            })
            messages.append(f"\nAssistant: {raw_response}\n")
            messages.append(f"\nTool result: {error_msg}\n")
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

        # Add this exchange to the conversation so the AI sees
        # what happened and can decide the next step
        result_str = json.dumps(result, indent=2, default=str)
        messages.append(f"\nAssistant: {raw_response}\n")
        messages.append(f"\nTool '{action}' returned:\n{result_str}\n")

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
    Remove very large fields to keep the response manageable.
    """
    clean = {}
    for key, value in state.items():
        if key == "identity":
            clean[key] = {"loaded": True, "name": value.get("personal", {}).get("name", "Unknown")}
        elif key == "tailored_resume":
            clean[key] = {k: v for k, v in value.items() if k != "company_research"}
        else:
            clean[key] = value
    return clean
