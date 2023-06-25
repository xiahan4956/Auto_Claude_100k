from autogpt.config import Config
import time

# Claude
MAX_TOKEN_ONCE = 100000
CONTINUE_PROMPT = "... continue"
import anthropic as anthropic


def _sendReq(client, prompt, max_tokens_to_sample):
    CFG = Config()
    for _ in range(5):
        try:
            response = client.completion(
                prompt=prompt,
                stop_sequences = [anthropic.HUMAN_PROMPT, anthropic.AI_PROMPT],
                model=CFG.smart_llm_model,
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
