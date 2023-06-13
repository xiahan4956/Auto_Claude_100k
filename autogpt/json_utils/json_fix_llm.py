"""This module contains functions to fix JSON strings generated by LLM models, such as ChatGPT, using the assistance
of the ChatGPT API or LLM models."""
from __future__ import annotations

import contextlib
import json
from typing import Any, Dict

from colorama import Fore
from regex import regex

from autogpt.config import Config
from autogpt.json_utils.json_fix_general import correct_json
from autogpt.llm import call_ai_function
from autogpt.logs import logger
from autogpt.speech import say_text

JSON_SCHEMA = """
{
    "thoughts":
    {
        "text": "thought",
        "reasoning": "reasoning",
        "plan": "- short bulleted\n- list that conveys\n- long-term plan",
        "criticism": "constructive self-criticism",
        "speak": "thoughts summary to say to user"
    },
    "command": {
        "name": "command name",
        "args": {
            "arg name": "value"
        }
    }
}
"""

CFG = Config()


def auto_fix_json(json_string: str, schema: str) -> str:
    """Fix the given JSON string to make it parseable and fully compliant with
        the provided schema using GPT-3.

    Args:
        json_string (str): The JSON string to fix.
        schema (str): The schema to use to fix the JSON.
    Returns:
        str: The fixed JSON string.
    """
    # Try to fix the JSON using GPT:




    # 额外处理json_string,防止过长,仅仅保留后面的部分
    json_string = json_string[-10000:]

    function_string = "def fix_json(json_string: str, schema:str=None) -> str:"
    args = [f"'''{json_string}'''", f"'''{schema}'''"]
    description_string = (

        '''
        This function takes a JSON string and ensures that it
        is parseable and fully compliant with the provided schema. If an object
        or field specified in the schema isn't contained within the correct JSON,
        it is omitted. The function also escapes any double quotes within JSON
        string values to ensure that they are valid. If the JSON string contains
        any None or NaN values, they are replaced with null before being parsed.

        ** if the command is the same as command before,you should switch to a new command ** 
        **if the command that you are parsing is null or blank or 'command name',you must add a command based on the meaning of the context**:
        Commands:
        1. append_to_file: Append to file, args: "filename": "<filename>", "text": "<text>"
        2. delete_file: Delete file, args: "filename": "<filename>"
        3. list_files: List Files in Directory, args: "directory": "<directory>"
        4. read_file: Read file, args: "filename": "<filename>"
        5. write_to_file: Write to file, args: "filename": "<filename>", "text": "<text>"
        6. google: Google Search, args: "query": "<query>"
        7. browse_website: Browse Website, args: "url": "<url>", "question": "<what_you_want_to_find_on_website>"
        8. delete_agent: Delete GPT Agent, args: "key": "<key>"
        9. get_hyperlinks: Get text summary, args: "url": "<url>"
        10. get_text_summary: Get text summary, args: "url": "<url>", "question": "<question>"
        11. list_agents: List GPT Agents, args: () -> str
        12. message_agent: Message GPT Agent, args: "key": "<key>", "message": "<message>"
        13. start_agent: Start GPT Agent, args: "name": "<name>", "task": "<short_task_desc>", "prompt": "<prompt>"
        14. task_complete: Task Complete (Shutdown), args: "reason": "<reason>"
        15. ask_genius_bing: "Ask Bing AI", args: "question": "<question>"
        
        **Return the json directly.**
        Do not give python code.
        Do not speak more.
        '''
    )

    # If it doesn't already start with a "`", add one:
    if not json_string.startswith("`"):
        json_string = "```json\n" + json_string + "\n```"
    result_string = call_ai_function(
        function_string, args, description_string, model=CFG.fast_llm_model
    )
    logger.debug("------------ JSON FIX ATTEMPT ---------------")
    logger.debug(f"Original JSON: {json_string}")
    logger.debug("-----------")
    logger.debug(f"Fixed JSON: {result_string}")
    logger.debug("----------- END OF FIX ATTEMPT ----------------")

    try:
        json.loads(result_string)  # just check the validity
        return result_string
    except json.JSONDecodeError:  # noqa: E722
        # Get the call stack:
        # import traceback
        # call_stack = traceback.format_exc()
        # print(f"Failed to fix JSON: '{json_string}' "+call_stack)
        return "failed"


def fix_json_using_multiple_techniques(assistant_reply: str) -> Dict[Any, Any]:
    """Fix the given JSON string to make it parseable and fully compliant with two techniques.

    Args:
        json_string (str): The JSON string to fix.

    Returns:
        str: The fixed JSON string.
    """
    assistant_reply = assistant_reply.strip()
    if assistant_reply.startswith("```json"):
        assistant_reply = assistant_reply[7:]
    if assistant_reply.endswith("```"):
        assistant_reply = assistant_reply[:-3]
    try:
        return json.loads(assistant_reply)  # just check the validity
    except json.JSONDecodeError:  # noqa: E722
        pass

    if assistant_reply.startswith("json "):
        assistant_reply = assistant_reply[5:]
        assistant_reply = assistant_reply.strip()
    try:
        return json.loads(assistant_reply)  # just check the validity
    except json.JSONDecodeError:  # noqa: E722
        pass

    # Parse and print Assistant response
    assistant_reply_json = fix_and_parse_json(assistant_reply)
    logger.debug("Assistant reply JSON: %s", str(assistant_reply_json))
    if assistant_reply_json == {}:
        assistant_reply_json = attempt_to_fix_json_by_finding_outermost_brackets(
            assistant_reply
        )

    logger.debug("Assistant reply JSON 2: %s", str(assistant_reply_json))
    if assistant_reply_json != {}:
        return assistant_reply_json

    logger.error(
        "Error: The following AI output couldn't be converted to a JSON:\n",
        assistant_reply,
    )
    if CFG.speak_mode:
        say_text("I have received an invalid JSON response from the OpenAI API.")

    return {}


def fix_and_parse_json(
    json_to_load: str, try_to_fix_with_gpt: bool = True
) -> Dict[Any, Any]:
    """Fix and parse JSON string

    Args:
        json_to_load (str): The JSON string.
        try_to_fix_with_gpt (bool, optional): Try to fix the JSON with GPT.
            Defaults to True.

    Returns:
        str or dict[Any, Any]: The parsed JSON.
    """

    with contextlib.suppress(json.JSONDecodeError):
        json_to_load = json_to_load.replace("\t", "")
        return json.loads(json_to_load)

    with contextlib.suppress(json.JSONDecodeError):
        json_to_load = correct_json(json_to_load)
        return json.loads(json_to_load)
    # Let's do something manually:
    # sometimes GPT responds with something BEFORE the braces:
    # "I'm sorry, I don't understand. Please try again."
    # {"text": "I'm sorry, I don't understand. Please try again.",
    #  "confidence": 0.0}
    # So let's try to find the first brace and then parse the rest
    #  of the string
    try:
        brace_index = json_to_load.index("{")
        maybe_fixed_json = json_to_load[brace_index:]
        last_brace_index = maybe_fixed_json.rindex("}")
        maybe_fixed_json = maybe_fixed_json[: last_brace_index + 1]
        return json.loads(maybe_fixed_json)
    except (json.JSONDecodeError, ValueError) as e:
        return try_ai_fix(try_to_fix_with_gpt, e, json_to_load)


def try_ai_fix(
    try_to_fix_with_gpt: bool, exception: Exception, json_to_load: str
) -> Dict[Any, Any]:
    """Try to fix the JSON with the AI

    Args:
        try_to_fix_with_gpt (bool): Whether to try to fix the JSON with the AI.
        exception (Exception): The exception that was raised.
        json_to_load (str): The JSON string to load.

    Raises:
        exception: If try_to_fix_with_gpt is False.

    Returns:
        str or dict[Any, Any]: The JSON string or dictionary.
    """
    if not try_to_fix_with_gpt:
        raise exception
    if CFG.debug_mode:
        logger.warn(
            "Warning: Failed to parse AI output, attempting to fix."
            "\n If you see this warning frequently, it's likely that"
            " your prompt is confusing the AI. Try changing it up"
            " slightly."
        )
    # Now try to fix this up using the ai_functions
    ai_fixed_json = auto_fix_json(json_to_load, JSON_SCHEMA)

    if ai_fixed_json != "failed":
        return json.loads(ai_fixed_json)
    # This allows the AI to react to the error message,
    #   which usually results in it correcting its ways.
    # logger.error("Failed to fix AI output, telling the AI.")
    return {}


def attempt_to_fix_json_by_finding_outermost_brackets(json_string: str):
    if CFG.speak_mode and CFG.debug_mode:
        say_text(
            "I have received an invalid JSON response from the OpenAI API. "
            "Trying to fix it now."
        )
        logger.error("Attempting to fix JSON by finding outermost brackets\n")

    try:
        json_pattern = regex.compile(r"\{(?:[^{}]|(?R))*\}")
        json_match = json_pattern.search(json_string)

        if json_match:
            # Extract the valid JSON object from the string
            json_string = json_match.group(0)
            logger.typewriter_log(
                title="Apparently json was fixed.", title_color=Fore.GREEN
            )
            if CFG.speak_mode and CFG.debug_mode:
                say_text("Apparently json was fixed.")
        else:
            return {}

    except (json.JSONDecodeError, ValueError):
        if CFG.debug_mode:
            logger.error(f"Error: Invalid JSON: {json_string}\n")
        if CFG.speak_mode:
            say_text("Didn't work. I will have to ignore this response then.")
        logger.error("Error: Invalid JSON, setting it to empty JSON now.\n")
        json_string = {}

    return fix_and_parse_json(json_string)
