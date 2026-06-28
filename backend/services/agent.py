"""Agent loop using Groq tool calling to draft customer replies."""

import json
import logging
import os

from fastapi import HTTPException
from groq import AsyncGroq

logger = logging.getLogger(__name__)

MODEL = "llama-3.3-70b-versatile"

# ── Mock Tools ────────────────────────────────────────────────────────────────

def search_knowledge_base(query: str) -> str:
    """Mock knowledge base search."""
    logger.info("Agent Tool called: search_knowledge_base(query=%r)", query)
    lower_query = query.lower()
    if "password" in lower_query or "reset" in lower_query:
        return "KB_ARTICLE_42: To reset your password, visit https://example.com/reset and enter your email address. A secure link will be sent to you."
    if "refund" in lower_query or "cancel" in lower_query:
        return "KB_ARTICLE_89: Refunds are processed within 3-5 business days. Cancellation can be done directly from the Settings -> Billing dashboard."
    if "address" in lower_query or "billing" in lower_query:
        return "KB_ARTICLE_12: To update your billing address, go to Settings -> Billing -> Update Info."
    return "No relevant knowledge base articles found."

def check_customer_account(ticket_id: str) -> str:
    """Mock customer account lookup."""
    logger.info("Agent Tool called: check_customer_account(ticket_id=%r)", ticket_id)
    return "Account Status: Active. Plan: Enterprise. Lifetime value: $15,000. Last login: 2 hours ago."

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Searches the company knowledge base for answers to customer questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query based on the customer's issue (e.g., 'how to reset password')",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_customer_account",
            "description": "Retrieves account details for the customer associated with the ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ticket ID to look up (e.g., 'T-1001')",
                    }
                },
                "required": ["ticket_id"],
            },
        },
    },
]

AVAILABLE_FUNCTIONS = {
    "search_knowledge_base": search_knowledge_base,
    "check_customer_account": check_customer_account,
}

SYSTEM_PROMPT = """\
You are an expert, professional customer support agent.
Your goal is to draft a helpful, empathetic reply to the customer's ticket.
You MUST use your provided tools to search the knowledge base for accurate answers or check account details before answering.
Once you have gathered the necessary information using tools, formulate the final draft reply.
Keep the draft concise, polite, and directly address the user's problem based on the knowledge base or account data.
Do not use markdown blocks for the final answer, just plain text ready to be sent to the customer.
"""

async def generate_draft_reply(ticket_id: str, text: str, scores: dict) -> str:
    """Run an agent loop to draft a reply using tools.

    Args:
        ticket_id: The unique ID of the ticket.
        text: The raw ticket text from the customer.
        scores: The dictionary of scores from the classification step.

    Returns:
        A string containing the AI-drafted reply.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY not configured for Agent.")
        return "Error: GROQ_API_KEY not configured."

    client = AsyncGroq(api_key=api_key)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Please draft a reply for Ticket ID: {ticket_id}\n\nCustomer says:\n{text}\n\nNote: The customer's tone is '{scores.get('tone', 'neutral')}'. Adjust your empathy accordingly.",
        },
    ]

    try:
        # Loop up to 5 times to prevent infinite loops
        for step in range(5):
            logger.info("Agent Loop Step %d for ticket %s", step + 1, ticket_id)
            
            response = await client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=1024,
                temperature=0.2,
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Convert response message to a dictionary before appending
            # The Groq SDK returns an object, but we need to append a dict to `messages`
            msg_dict = {"role": "assistant"}
            if response_message.content:
                msg_dict["content"] = response_message.content
            if tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            
            messages.append(msg_dict)

            if tool_calls:
                # Execute tools
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = AVAILABLE_FUNCTIONS.get(function_name)
                    if not function_to_call:
                        continue
                    
                    function_args = json.loads(tool_call.function.arguments)
                    function_response = function_to_call(**function_args)
                    
                    # Append tool result
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
            else:
                # No more tools to call, we have the final drafted reply
                logger.info("Agent Loop completed successfully for %s", ticket_id)
                return response_message.content or "Error: Agent returned an empty response."

        return "Agent could not formulate a reply within the step limit."
    except Exception as exc:
        logger.error("Agent Loop failed: %s", exc)
        return "Failed to generate draft reply due to an error."
