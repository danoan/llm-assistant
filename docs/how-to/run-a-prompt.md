# How to run a prompt

The `llm-assistant` can run prompts that are located in a prompts collection
folder. It is possible to execute prompts using the CLI in an interactive
way or using the `llm-assistant` API.

## Prompt collection folder

In the `llm-assistant-config.toml` file you should register the location of
the prompt collection folder in the `[prompt]` section.

```toml
[prompt]
prompt_collection_folder = "path/to/prompt-collection-folder"
```

The path is relative to the `llm-assistant-config.toml` path. It is expected
that each prompt in the collections folder has its own directory and at least
one file name `config.toml`

```
prompt-collection-folder
    - correct-text
        - config.toml
    - word-definition
        - config.toml
```

The `config.toml` file should look similar to the following:

```toml
name="Alternative Expressions"
system_prompt='''
You are fluent speaker of the {language} language and your task is to list at most five expressions that encodes the meaning of a sentence or a word enclosed by double angle brackets.

Your response must be given as a json list and the items must be written in {language}.

'''
user_prompt='''
Language: {language}
Sentence: <<{message}>>
Response:
'''
```
You can associate a git namespace to your prompts collection folder and keep them synced with the
help of `prompt-manager`. Check [](sync-and-push-prompts.md) for more information.

## Running a custom prompt

To run a prompt, the same must be located in the prompt-collection folder. Consider the 
`alternative-expression` prompt given in the previous section. There are three alternatives
to run it.

```bash
echo "{}" | llm-assistant run alternative-expression --p language portuguese --p message "ganhar a vida"
echo '{"message":"ganhar a vida"}' | llm-assistant run alternative-expression --p language portuguese
echo '{"message":"ganhar a vida", "language":"portuguese"}' | llm-assistant run alternative-expression
```

## Running a prompt interactively

You are invited to select one of the prompts located at `prompt.prompt_collection_folder` and then to load or
create a new instance for the prompt.

**Prompt Instance**: A prompt instance is a subset of pre-defined prompt variables. For example, in the alternative-expression
prompt, we could have a french instance (language=french) and a portuguese instance (language=portuguese).


:::{tip}
Instances are stored at `${LLM_ASSISTANT_CONFIGURATION_FOLDER}/prompts/instances`
:::

```bash
╭────────────────────────────────────────────────────────────────────────────────────────╮
│ Select prompt                                                                          │
╰────────────────────────────────────────────────────────────────────────────────────────╯
1. Alternative Expressions 2. Word Definition

Prompt index: 2
╭────────────────────────────────────────────────────────────────────────────────────────╮
│ Choose an option                                                                       │
╰────────────────────────────────────────────────────────────────────────────────────────╯
1. New instance 2. Load instance

Option index: 1
Enter the instance name: portuguese
Enter variable assignment: language=portuguese
╭─────────────────────────────────────── New Chat ───────────────────────────────────────╮
│ Prompt: Word Definition                                                                │
│ Instance:portuguese                                                                    │
╰────────────────────────────────────────────────────────────────────────────────────────╯
Enter messaó
Enter message: $$
╭───────────────────────────── Word Definition::portuguese ─────────────────────────────╮
│ borogodó                                                                              │
╰───────────────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────────── Word Definition::portuguese ─────────────────────────────╮
│ [                                                                                     │
│   "Encanto, atração irresistível e misteriosa; charme",                               │
│   "Qualidade ou característica que atrai e seduz de maneira peculiar ou especial.",   │
│   "Dom, habilidade natural para seduzir ou encantar as pessoas.",                     │
│   "Magia, feitiço; algo que exerce influência sobre os outros de forma inexplicável." │
│ ]                                                                                     │
╰───────────────────────────────────────────────────────────────────────────────────────╯
```


## Running a prompt using the API

You can also run prompts using the `llm-assistant` python API.

```python
config = model.RunnerConfiguration(openai_key, "gpt-3.5-turbo", True, "path-to-cache-file")
api.LLMAssistant().setup(config)

prompt_configuration = model.PromptConfiguration(
    "alternative-expression", "system_prompt", "user_prompt"
)

data = {
    "language":"portuguese" ,
    "message": "ganhar a vida"
}

api.custom(prompt_configuration, **data)
```

