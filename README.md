# Applications

Below examples demonstrates the capability of EvaDB in extracting embedding from texts, building similarity index, searching similar sources, and using **local LLM** to answer question based on that. These apps are powered by EvaDB and GPT4All. No OpenAI API Key is necessary.

## Story Question and Answering
For this example, we use "War and Peace" story as the source for our demonstration purpose.

## Repository based Question and Answering
In this example, we use "swyxio/ai-notes" github repository as the source. User can ask any question pertaining to various topics in AI(Speech Recognition, Reinforcement Learning Techniques, Computer Vision etc.). Users can even ask for useful links to these topics.

# Setup
Ensure that the local Python version is >= 3.8. Install the required libraries:

```bash
pip install -r requirements.txt
```

## How to Run Story Question and Answering
```bash
python evadb_qa.py
```

## How to Run Repository based Question and Answering
```bash
python evadb_ai_repo_qa.py {model_name} {Question}
```
