# How to sync and push prompts

The `llm-assistant` comes with a `prompt-manager` command that allows you to
do prompt versioning. 

## Prompt syncing

To enable prompt-versioning, you should first register a git namespace where your 
prompts are stored and list the prompts you want to pull from the repository.

```toml
# llm-assistant-config.toml
[prompt]
git_user = "danoan/prompts"

[prompt.versioning]
correct-text="2.1.0"
```

Next, you run

```bash
prompt-manager versioning sync
```

In the example above, the prompt `correct-text` will be pulled and stored at the specified
prompt collection folder and it will be checkout in version 2.1.0.

:::{tip}
If the version number is an empty string or the word `last`, the last version of the
prompt is checkout.
:::

From this point, the prompt `correct-text` is available to run by `llm-assistant`. 

## Pushing a new prompt version

It is likely the case that when working in your project you realize that some
of your prompts need some adjustments. The `prompt-manager` offers the command
`push` to help you with that.

You can think of `push` as a wizard that wraps some of the git functionalities
to help enforcing a versioning policy and structure of your prompts.

Let us say that you add a new file `apple` in prompt `correct-text` and you
decided to create a new version for this prompt. Then, you just need to 
execute:

```bash
prompt-manager versioning push correct-text
```

to start the wizard. The following steps will be taken:

1. **Describe the changes**: These changes are going to be added in the
   README.md file of the prompt, which also plays the role of a changelog.
2. **Base version**: Which version you want to update?
3. **Nature of Changes**: Whether the suggested version will advance the 
   major, the minor or the fix counter.
4. **Suggested Version**: To accept the suggested version or enter a new one.
5. **Git operations**:
    - Checkout master;
    - Update the changelog and commit;
    - Push master branch;
    - Checkout to the suggested version branch.
6. **Select the changes to be added**: It is a wrapper around `git add -i`.
   Here it is where you select which changes are going to be part of 
   the new version.
7. **Git operations**:
    - Commit changes;
    - Push branch;
    - Create and push tag.

Below there is an example of the wizard:

```bash
prompt-manager versioning push prompt-test
Fetching repository data
Describe the changes (finish the input by outputing a line with $$)
Add apple
$$
╭───────────────────────────────── Current versions ──────────────────────────────────╮
│ 1. 1.0.0                                                                            │
╰─────────────────────────────────────────────────────────────────────────────────────╯
Enter a base version (1.0.0): 
╭──────────────────────────────── Nature of Changes ──────────────────────────────────╮
│ 1. Prompt tweak: Add extra examples, edit intructions to be more                    │
│    precise about some aspect or remove ambiguity.                                   │
│ 2. Interface update: The expected input values or the output format has changed.    │
│ 3. Scope change: The prompt become more specialized or more general                 │
╰─────────────────────────────────────────────────────────────────────────────────────╯

What is the nature of the changes? 1

Suggested version (1.0.1): 

Checkout existing branch: master
Commiting changes: Update changelog: Add 1.0.1
Pushing branch: master
Checkout existing branch: v1.0

*** Commands ***
  1: status	  2: update	  3: revert	  4: add untracked
  5: patch	  6: diff	  7: quit	  8: help
What now> 4
          indexé  non-indexé chemin
  1: apple
Add untracked>> 1
          indexé  non-indexé chemin
* 1: apple
Add untracked>> 
1 chemin ajouté

*** Commands ***
  1: status	  2: update	  3: revert	  4: add untracked
  5: patch	  6: diff	  7: quit	  8: help
What now> 7
Au revoir.
Commiting changes: Release version 1.0.1
Pushing branch: v1.0
Creating tag: v1.0.1
```

