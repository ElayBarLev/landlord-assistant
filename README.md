# Landlord assistant

A Claude Desktop (Cowork) plugin for a landlord with several buildings. Six skills, two agents, one folder of memory.

- **The folder** (`My Properties`, on her computer) holds all her data. It is never in this repository.
- **The plugin** (this repository) holds only generic instructions. Updates replace these and never her folder.

Never commit tenant names, addresses, leases or ledgers here.

## One-time setup, about 15 minutes on a screen share

She needs a paid Claude plan and [Claude Desktop](https://claude.com/download) on Mac or Windows. Labels may differ slightly by app version.

1. **Folder.** Create `My Properties` in Documents. For off-computer backup put it inside OneDrive, iCloud Drive or Google Drive, set to "always keep on this device".
2. **Plugin.** Cowork tab > Customize > Plugins > Add > Add marketplace > Add from a repository: `ElayBarLev/landlord-assistant`. Install **landlord**.
3. **Auto-update.** On that marketplace turn on **Sync automatically**. If it asks for GitHub, follow the prompt and grant the Claude GitHub App access to this repository only.
4. **Project.** Cowork > Projects > + > Use an existing folder > `My Properties`. Paste these project instructions once (they never need to change):

   > I am a landlord. My memory is the My Properties folder. At the start of every task use the landlord plugin's start skill, before answering. Save lasting facts to the folder with the remember skill. Draft messages but never send them. Never delete my files.

5. **Permissions.** Keep approval on for actions outside the folder. Do not enable "Skip all approvals".
6. **Model.** Choose Sonnet, not the largest model. It uses less of her limit.
7. **First chat.** In the project she writes "Set me up". Old chats can be pasted one building at a time.
8. **Prove auto-update before hanging up.** Run `./release.sh "Test update"` here. Wait, start a new task, ask "Which version are you?". If it still shows the old one, press **Check for updates** and see whether that works.

## Habits for her

- Work inside the **My Properties** project, with the Claude app open.
- One topic, one task. Start a new one freely: the folder remembers.
- Drop documents into `inbox` instead of pasting them.
- Once a month: "Do my monthly review".

## Publish a change

Edit on `main`, then `./release.sh "what changed"`. It validates, tests, raises the version and pushes; a failed check pushes nothing. She gets it in a new task after the sync.

Undo: `git revert --no-edit HEAD && ./release.sh "Undo last change"`.

## Known limits

- The sync interval for personal marketplaces is undocumented, and users have reported stuck updates. The monthly checkup compares versions and tells her which button to press.
- Not a lawyer or accountant. It drafts, she decides.
- Files Claude opens are processed on Anthropic's servers. Keep bank logins and ID scans out of the folder.
