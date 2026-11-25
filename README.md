 # Landlord assistant

A Claude Desktop (Cowork) plugin for a landlord with several buildings. Seven skills, two agents, one folder of memory, and a program that catalogs her existing files without changing them.

- **The folder** (`My Properties`, on her computer) holds all her data. It is never in this repository.
- **The plugin** (this repository) holds only generic instructions. Updates replace these and never her folder.

Never commit tenant names, addresses, leases or ledgers here.

## Before the call (you, once)

Auto-sync needs the Claude GitHub App on this repository, even though it is public. Sign in to GitHub as the owner, open <https://github.com/apps/claude>, install it, choose **Only select repositories**, and select only `landlord-assistant`.

## One-time setup on a screen share, about 45 minutes

She needs a paid Claude plan, the newest [Claude Desktop](https://claude.com/download), Windows or Mac, and a backup of her files. Update the app first: an older version could damage files while creating a project from a folder. Labels move between versions.

### A. Memory folder and Claude

1. Create an empty folder `My Properties` in Documents.
2. **Plugin.** Customize > Plugins > Add > Add marketplace > Add from a repository: `ElayBarLev/landlord-assistant`. Install **landlord**. Turn on **Sync automatically**.
3. **Project.** In the desktop app (not the website): Projects > **New project** (or **+**) > **Use a folder** or **Use an existing folder** > `My Properties`. Attach no files. No folder button? Start a new conversation, **Add folder** under the message box, `My Properties`.
4. **Connect only `My Properties`.** Never connect Documents or the whole disk: Claude can change whatever is connected.
5. **Instructions.** Paste once into the project's instructions (or Settings > Instructions for Claude):

   > I am a landlord. My memory is the My Properties folder. At the start of every task about my properties use the landlord plugin's start skill, before answering. Save lasting facts to the folder with the remember skill. Draft messages but never send them. Never delete my files.

6. Keep the mode that asks before acting. Choose Sonnet.
7. She types "Set me up". Then open `HOME.md` on her computer and check it has her answers.

### B. Library of her existing files

The library program runs on her computer. It opens her files for reading only and writes only in `My Properties/library` and its own folder. It is not updated automatically, on purpose: it can read her files, so a person decides.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) with the command on that page for her system. Open a new terminal.
2. Install the program from a fixed version:

   ```
   uv tool install --python 3.12 "landlord-library @ https://github.com/ElayBarLev/landlord-assistant/archive/refs/tags/VERSION.zip#subdirectory=librarian"
   uv tool update-shell
   ```
   Replace `VERSION` with a tag from this repository, such as `v1.0.1`.
3. New terminal: `landlord-library setup`. It looks in Documents, Desktop, Downloads, Pictures and OneDrive. For other places add `--root "D:\Houses"` (repeat it; this replaces the defaults). It reads only names now, and then runs every hour.
   - Mac: allow access if asked. If the hourly run cannot read Documents, allow it in System Settings > Privacy & Security.
   - Scans: without Tesseract, Claude looks at small page images instead. With Tesseract installed, add for example `--languages por+eng`.
4. In Claude: "Look at my computer and tell me how my files are organized." She approves folders. Only those are read.
5. After an hour, or `landlord-library run`: "Describe the first documents." Continue in batches over days.

### C. Prove auto-update

Publish a change here, wait, start a new conversation, ask "Which landlord version are you?". If it is old, press **Check for updates** and try again.

## Obsidian

Not required. The library is ordinary Markdown with properties, so she or you can open `My Properties` as a vault in [Obsidian](https://obsidian.md) (free) to browse. `library/Documents.base` is a table of all documents. Turn off nothing, add no plugins.

## Adding files later

- Any new file in an approved folder is picked up by itself.
- New documents to act on now: drop in `inbox`, then "I put a document in the inbox".
- Boxes of paper: "Box 3 in the attic has Main St receipts 1985-1992".

## Remove

`uv tool uninstall landlord-library`. Windows: `schtasks /Delete /TN LandlordLibrary`. Mac: delete `~/Library/LaunchAgents/landlord.library.plist`. Her files are unaffected.

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
- The library skips cloud-only files, very large files, hidden and system folders, and files named like passwords or passports. It removes card numbers and IBANs from text, not from images. Old .doc and .xls files are listed by name only.
- Page images and text of approved folders are copied into `My Properties/library`. Files Claude opens are processed on Anthropic's servers. Keep bank logins and ID scans out of the folder.
