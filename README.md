# Landlord assistant

A Claude Desktop (Cowork) plugin for a landlord with several buildings. Seven skills, two agents, one folder of memory.

- **The folder** (`My Properties`, on her computer) holds all her data. It is never in this repository.
- **The plugin** (this repository) holds only generic instructions. Updates replace these and never her folder.

Never commit tenant names, addresses, leases or ledgers here.

## Before the call (you, once)

Auto-sync needs the Claude GitHub App on this repository, even though it is public. Sign in to GitHub as the owner, open <https://github.com/apps/claude>, install it, choose **Only select repositories**, and select only `landlord-assistant`.

## One-time setup, about 30 minutes on a screen share

She needs a paid Claude plan and the newest [Claude Desktop](https://claude.com/download) on Mac or Windows. Update the app first: an older version could damage files while creating a project from a folder. Labels move between versions.

1. **Folder.** Create `My Properties` in Documents, with a folder `old-files` inside. Put everything inside this one folder, because some versions allow only one folder per project.
2. **Plugin.** Customize > Plugins > Add > Add marketplace > Add from a repository: `ElayBarLev/landlord-assistant`. Install **landlord**.
3. **Auto-update.** On that marketplace turn on **Sync automatically**. If it asks for a GitHub account or access, see Known limits.
4. **Project with a folder.** In the desktop app (not the website): Projects > **New project** (or **+**) > **Use a folder** or **Use an existing folder** > choose `My Properties`. Attach no files in that window. The note that the project stays on this computer is expected.
   - A project made before, or on the website, may only accept files. Make a new one.
   - No folder button? Skip projects: start a new conversation, choose **Add folder** under the message box, pick `My Properties`. Memory is in the folder, so it works the same.
5. **Instructions.** Paste once into the project's instructions. Without a project, paste into Settings > Instructions for Claude.

   > I am a landlord. My memory is the My Properties folder. At the start of every task about my properties use the landlord plugin's start skill, before answering. Save lasting facts to the folder with the remember skill. Draft messages but never send them. Never delete my files.

6. **Permissions.** Keep the mode that asks before acting. Do not skip approvals.
7. **Model.** Choose Sonnet, not the largest model.
8. **First chat.** "Set me up". One building at a time.
9. **Check that the folder really works.** Open `HOME.md` in `My Properties` on her computer: it must contain what she just said. Start a new conversation and ask about a tenant.
10. **Prove auto-update.** Publish a change here, wait, start a new conversation, ask "Which landlord version are you?". If it is old, press **Check for updates** and try again.

## Adding files

- **New documents** (this month's lease, bill): drop in `inbox`, then "I put a document in the inbox".
- **Decades of old files:** back them up, then copy (do not move) into `old-files`, any structure, then "I added old files". Claude catalogs names and duplicates without reading them, asks what matters, and reads in small batches.
- **Paper:** scan to searchable PDF, one document per file, building and year in the name. Unscanned boxes: "Box 3 in the attic has Main St receipts 1985-1992".
- Do not upload files into the project's own file list. That makes static copies.
- If the folder is in OneDrive, iCloud or Google Drive, mark it "always keep on this device".
- Leave out ID copies, bank logins and full bank statements.

## Habits for her

- Work in the **My Properties** project (or add the folder), with the Claude desktop app open. The website and phone cannot open the folder by themselves.
- One topic, one task. Start a new one freely: the folder remembers.
- Drop documents into `inbox` instead of pasting them.
- Once a month: "Do my monthly review".

## Publish a change

Edit on `main`, then `./release.sh "what changed"`. It validates, tests, raises the version and pushes; a failed check pushes nothing. She gets it in a new task after the sync.

Undo: `git revert --no-edit HEAD && ./release.sh "Undo last change"`.

## Known limits

- **Sync automatically** may require a GitHub account connected in her Claude that can access this repository, possibly with admin rights. If that is not possible, the fallback is pressing **Check for updates** once a month. Connecting your own GitHub in her Claude would let it reach whatever the GitHub App can see, so limit the App to this repository.
- The sync interval for personal marketplaces is undocumented, and users have reported stuck updates. The monthly checkup compares versions and tells her which button to press.
- Not a lawyer or accountant. It drafts, she decides.
- Files Claude opens are processed on Anthropic's servers. Keep bank logins and ID scans out of the folder.
