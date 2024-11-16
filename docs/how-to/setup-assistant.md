# How to setup llm-assistant

The `llm-assistant` uses a configuration file called `llm-assistant-config.toml`
to execute its commands. It looks for this file in two different ways.

## Lookup mechanism

The `llm-assistant` will first check if there is any configuration file in the current
working directory. If such file does not exist, then it will backtrack the folder
hierarchy, starting from the working directory, searching for a configuration file. If
arriving at the root of the hierarchy no configuration file is found, then it checks the
contents of the environment variable `LLM_ASSISTANT_CONFIGURATION_FOLDER`.

## Local configuration file

An alternative way to configure `llm-assistant` is by creating the `llm-assistant-config.toml`
in the same directory `llm-assistant` is executed. To do that, run

```bash
llm-assistant setup init
```

## Environment variable configuration

You should set the environment variable `LLM_ASSISTANT_CONFIGURATION_FOLDER` to
point to a directory where the configuration files will be stored.

```bash
export LLM_ASSISTANT_CONFIGURATION_FOLDER="~/.config/llm-assistant"
```

Next, you should run:

```bash
llm-assistant setup init --env
```

This creates the file `${LLM_ASSISTANT_CONFIGURATION_FOLDER}/llm-assistant-config.toml`
which contains settings regarding which LLM to use and which prompt repository to use.

After that, you can always run `llm-assistant setup` to print the information contained
in the configuration file.


:::{Tip}
In both cases, you can use the flag `--force` to reset an existing configuration file.
:::
