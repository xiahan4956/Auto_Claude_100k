from autogpt.config import Config
import time
import openai
import json

CFG = Config()
openai.api_key = CFG.openai_api_key


MAX_TOKEN_ONCE = 100000
CONTINUE_PROMPT = "... continue"
import anthropic as anthropic


def _sendReq(client, prompt, max_tokens_to_sample):
    print("----------------request----------------")
    print(rf"{prompt}")
    print("----------------request----------------\n")
    print("the input words of claude: "+str(len(prompt)))


    for _ in range(5):
        try:
            response = client.completion(
                prompt=prompt,
                stop_sequences = [anthropic.HUMAN_PROMPT, anthropic.AI_PROMPT],
                model="claude-1.3-100k",
                max_tokens_to_sample=max_tokens_to_sample,
                temperature = 0.3
            )
            break
        except Exception as e:
            print(e)
            time.sleep(1)
    return response

def sendReq(question, max_tokens_to_sample: int = MAX_TOKEN_ONCE):


    CFG = Config()
    client = anthropic.Client(CFG.claude_api_key)
    prompt = f"{question} {anthropic.AI_PROMPT}"

    response = _sendReq(client, prompt, max_tokens_to_sample)
    data = response["completion"]

    return data

def pmt_gpt_to_claude(question):
    question = str(question)[1:-1]
    question = question.replace("{\'role\': \'system\', \'content\':","\n\nHuman:")
    question = question.replace("{\'role\': \'user\', \'content\':","\n\nHuman:")
    question = question.replace("{\'role\': \'assistant\', \'content\':","\n\n\Assistant:")
    question = question.replace("\'}","")
    return question



def fix_claude_json(claude_resp):
    messages = [{"role":"system","content":r"1. You will receive a JSON string, and your task is to extract information from it and return it as a JSON object. 2.Use function's json schema to extrct.Please notice the format  3.  Be aware that the given JSON may contain errors, so you may need to infer the fields and the format from the JSON string. 4.Do not use \"   and you should use ' " },{"role": "user", "content": claude_resp}]
    functions = [
        {
            "name": "parse_claude_json",
            "description": "parse a claude response to the json",
            "parameters": {
                "type": "object",
                "properties": {
                    "thoughts": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "thoughts"
                            },
                            "reasoning": {
                                "type": "string"
                            },
                            "plan": {
                                "type": "string",
                                "description": "it is a string,not list.If you find it is list,please use correct it "
                            },
                            "criticism": {
                                "type": "string",
                                "description": "constructive self-criticism"
                            },
                            "speak": {
                                "type": "string",
                                "description": "thoughts summary to say to user"
                            }
                        },
                        "required": ["text", "reasoning", "plan", "criticism", "speak"],
                    },
                    "command": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "args": {
                                "type": "object"
                            }
                        },
                        "required": ["name", "args"],
                    }
                },
                "required": ["thoughts", "command"],
            },
            },
    ]
    
    for _ in range(10):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=messages,
                functions=functions,
                max_tokens=3000,
                temperature=0.0,
            )
            resp_json = response["choices"][0]["message"]["function_call"]["arguments"]
            break
        except Exception as e:
            time.sleep(1)
            print(e)

    # fix the plan
    try:
        resp_json = json.loads(resp_json)
        resp_json["thoughts"]["plan"] = str(resp_json["thoughts"]["plan"]).replace("[","").replace("]","")
        resp_json = json.dumps(resp_json)
    except Exception as e:
        print(e)

    return resp_json

