
from autogpt.config import Config


# Claude
MAX_TOKEN_ONCE = 100000
CONTINUE_PROMPT = "... continue"
import anthropic as anthropic

CFG = Config()

def _sendReq(client, prompt, max_tokens_to_sample):
    print("current words of Claude:",len(prompt))
    response = client.completion(
        prompt=prompt,
        stop_sequences = [anthropic.HUMAN_PROMPT, anthropic.AI_PROMPT],
        model=CFG.claude_mode,
        max_tokens_to_sample=max_tokens_to_sample,
    )
    return response

def sendReq(question, max_tokens_to_sample: int = MAX_TOKEN_ONCE):
    client = anthropic.Client(CFG.claude_api_key)
    prompt = f"{anthropic.HUMAN_PROMPT} {question} {anthropic.AI_PROMPT}"

    response = _sendReq(client, prompt, max_tokens_to_sample)
    data = response["completion"]
    prompt = prompt + response["completion"]

    while response["stop_reason"] == "max_tokens":
        prompt = prompt + f"{anthropic.HUMAN_PROMPT} {CONTINUE_PROMPT} {anthropic.AI_PROMPT}"
        response = _sendReq(client, prompt, max_tokens_to_sample)
        d = response["completion"]
        prompt = prompt + d
        if data[-1] != ' ' and d[0] != ' ':
            data = data + " " + d
        else:
            data = data + d
    return data