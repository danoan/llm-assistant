# Getting started with LLM Assistant

Collection of tools to work with LLMs.

## Features

- CLI for interactive prompt execution.
- Prompt versioning tool.
- Prompt definition format and general runner.


## How to use

### Configuring a LLM provider

The first step is to create a `llm-assistannt-config.toml` file
to hold runner and prompt settings.

```toml
[runner]
openai_key = "<OPENAI_KEY>"
model = "gpt-3.5-turbo"
use_cache = true
cache_path = "/home/user/.config/llm-assistant/cache.db"

[prompt]
git_user = "danoan-prompts"
prompt_collection_folder = "/home/user/.config/llm-assistant/cache.db"

[prompt.versioning]
alternative-expression = "v2.0.0"
word-definition = "v1.0.0"
```

**Configuration file search**: The application backtracks the current working directory searching for the
`llm-assistant-config.toml` file starting from CWD. If not such file is found, it searches in the location
specified by the environment variable `LLM_ASSISTANT_CONFIGURATION_FOLDER`.

You can check which configuration file is being used by running

```bash
llm-assistant setup
```


### Running a prompt

Consider the `alternative-expression` prompt configuration file:

```toml
name="Alternative Expressions"
system_prompt='''
You are fluent speaker of the {language} language and your task is to list at most five expressions that encodes the meaning of a sentence or a word enclosed by double angle brackets.

Your response must be given as a json list and the items must be written in {language}.

Examples
--------

Language: English.
Sentence: <<It is an unusual day today.>>
Response: [
    "It is an odd day today",
    "Today is quite unusual",
    "It is an atypical day",
    "Today feels out of the ordinary",
    "Today stands out differently"
]
--

Language: french
Sentence: <<gentil>>
Response: [
    "aimable",
    "doux"
]
--

'''
user_prompt='''
Language: {language}
Sentence: <<{message}>>
Response:
'''
```

It is possible to run the prompt in three different ways

```bash
echo "{}" | llm-assistant run alternative-expression --p language portuguese --p message "ganhar a vida"
echo '{"message":"ganhar a vida"}' | llm-assistant run alternative-expression --p language portuguese
echo '{"message":"ganhar a vida", "language":"portuguese"}' | llm-assistant run alternative-expression
```

### Starting an interactive session

To start an interactive session, type:

```bash
llm-assistant session
```

You are invited to select one of the prompts located at `prompt.prompt_collection_folder` and then to load or
create a new instance for the prompt.

**Prompt Instance**: A prompt instance is a subset of pre-defined prompt variables. For example, in the alternative-expression
prompt, we could have a french instance (language=french) and a portuguese instance (language=portuguese).

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

### Syncing prompts

The `sync` feature allows to fetch the most recent updates from the remote prompt repository
and to update the local view.

```bash
prompt-manager sync
```

The synchronization is done according with the `prompt.versioning` settings.

```toml
[prompt]
git_user = "danoan-prompts"
prompt_collection_folder = "/home/user/.config/llm-assistant/cache.db"

[prompt.versioning]
alternative-expression = "v2.0.0"
word-definition = "v1.0.0"
```

For the settings above, the sync will seach for the repositories:

- danoan-prompts/alternative-expression
- danoan-prompts/word-definition

on github and then fetch the specified version.

### Push prompt version assistant

The `prompt-manager versioning push` commands guides the user to the creation of a
new prompt version.


## Contributing

Please reference to our [contribution](http://danoan.github.io/llm-assistant/contributing) and [code-of-conduct]((http://danoan.github.io/llm-assistant/code-of-conduct.md)) guidelines.
