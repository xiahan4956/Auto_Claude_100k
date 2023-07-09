# Auto Bard
Use bard to run auto_gpt_0.4.2.
<video src="bard.mp4" controls title="Title"></video>


# How to start
1. clone auto_bard `git clone -b auto_bard_0.4.2 https://github.com/xiahan4956/Auto_Claude_100k.git`  
2. install dependencies. `pip install -r  requirements.txt` `pip install -r  bard_requirements.txt`
3. put your `service_account.json` in the root directory. the json file is your google cloud service account key.I get it by the lablab.ai emails
4. set `.env.templat`e to `.env` and fill in your openai api key. The program uses the ai function of the openai  to fix bard json
5. in the terminal. run `python -m autogpt`