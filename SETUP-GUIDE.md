# ArchiCAD AI Assistant — Setup Guide (Windows)

This lets you control **ArchiCAD** by typing plain-English instructions to **Claude** (an AI assistant), e.g. *"create a 5 by 4 metre room of walls."*

You only do this setup **once**. It takes about 15–20 minutes, most of which is waiting for downloads. You do **not** need to understand any of it — just follow the steps in order.

**Before you start, you need:**
- A Windows PC.
- **ArchiCAD 29** already installed. *(If you have a different ArchiCAD version, contact Adam — the add-on is built for 29.)*
- An internet connection.

---

## Step 1 — Install Claude Desktop (the AI app)

1. Go to **https://claude.ai/download**
2. Download the **Windows** version and run the installer (just keep clicking Next / Install).
3. Open Claude Desktop once and **sign in** (or create a free account) so it finishes setting up. Then you can close it.

---

## Step 2 — Run the one-time installer

This installs the "connector" that lets Claude talk to ArchiCAD. Pick **either** option:

### Option A — Easiest (copy & paste one line)
1. Click the **Windows Start** button, type **PowerShell**, and press **Enter**. A blue window opens.
2. Copy this entire line, paste it into the blue window (right-click to paste), and press **Enter**:

   ```
   irm https://raw.githubusercontent.com/agmurf/tapir-archicad-MCP/master/install.ps1 | iex
   ```

3. Wait. It will say things like *"Installing…"* and *"please wait."* The first time can take **5–10 minutes** (it downloads a lot). When it says **"Setup complete!"**, you're done with this step. Leave the window open — it lists the file you need in Step 3.

### Option B — If you'd rather not use PowerShell
1. Adam will send you a ZIP file (or a download link). Save it and **right-click → Extract All**.
2. Open the extracted folder and **double-click `Setup-Windows.bat`**.
3. Wait for **"Setup finished."**

---

## Step 3 — Load the ArchiCAD add-on

1. Open **ArchiCAD 29**.
2. In the top menu, click **Options → Add-On Manager…**
3. Click **Add…** (or "Edit List of Available Add-Ons" → Add).
4. Browse to this file and select it:

   ```
   C:\ArchitechMCP\addon\TapirAddOn_AC29_Win.apx
   ```

5. Make sure it appears **checked/enabled** in the list, then click **OK**.
6. If ArchiCAD asks to restart, let it.

---

## Step 4 — Load the ArchiCAD library (needed for doors & windows)

1. In ArchiCAD: **File → Libraries and Objects → Library Manager…**
2. Add the **standard ArchiCAD 29 library** if it isn't already there (it usually is for normal projects), then click **OK**.

*(If you skip this, everything still works except doors and windows.)*

---

## Step 5 — Start using it

1. Make sure **ArchiCAD is open with a project** (File → New → Create is fine).
2. **Fully quit Claude Desktop** if it's open: look at the bottom-right of your screen near the clock, click the small **^** arrow, **right-click the Claude icon → Quit**. Then open Claude Desktop again. *(Just closing the window isn't enough — it keeps running in the background.)*
3. In Claude Desktop, start a new chat and type:

   > **List my running ArchiCAD instances**

   After a few seconds it should reply with a **port number** (e.g. `19753`). 🎉 That means it's connected.

4. Now try building something — see **USAGE-MANUAL.md** for lots of examples. A good first one:

   > **On port 19753, create a 5 by 4 metre room of walls with a slab underneath.**

   *(Use whatever port number it told you in step 3.)*

---

## Keeping it up to date

When Adam publishes an improvement, update like this:
1. **Close ArchiCAD.**
2. Double-click **`C:\ArchitechMCP\Update.bat`** (or ask Adam to send it).
3. When it says *"Update complete,"* reopen ArchiCAD and **fully restart Claude Desktop** (Step 5.2).

---

## If something isn't working

- **"List my running ArchiCAD instances" says it can't / no port:**
  Wait ~30 seconds after opening Claude Desktop (it starts up slowly the first time), then ask again in a **new chat**. Make sure ArchiCAD is open with a project.
- **You closed and reopened Claude but nothing changed:** you probably only closed the window. Do a **full Quit** from the tray icon (Step 5.2).
- **Doors/windows fail:** do Step 4 (load the library).
- **Still stuck:** send Adam a screenshot of the Claude chat and what you typed.

---

*Built by Adam. Questions or problems → contact Adam.*
