from autogpt.config import Config
import time

# Claude
MAX_TOKEN_ONCE = 100000
CONTINUE_PROMPT = "... continue"
import anthropic as anthropic

CFG = Config()
def _sendReq(client, prompt, max_tokens_to_sample):
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
    prompt = f"{anthropic.HUMAN_PROMPT} {question} {anthropic.AI_PROMPT}"

    response = _sendReq(client, prompt, max_tokens_to_sample)
    data = response["completion"]

    return data
