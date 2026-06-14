# ArchiCAD AI Assistant — How to Use It

You type plain English to Claude Desktop and it builds in ArchiCAD for you. This manual shows **exactly what to say**, with examples you can copy.

---

## The 3 golden rules

1. **Have ArchiCAD open with a project** before you ask for anything.
2. **Start by getting the port number**, then include it in your requests:
   > List my running ArchiCAD instances

   It replies with a number like **19753**. Use that number in everything below (yours may differ).
3. **Be specific.** Give sizes and positions in **metres**, with the origin at (0,0). Vague requests get vague results; exact numbers get exact buildings.

> 💡 **Tip:** For anything bigger than a few elements, ask it to **preview first**: *"...but preview it first before creating."* It will show you counts and the size, and build nothing until you say go.

---

## Quick wins (copy these, change the numbers)

**A single wall**
> On port 19753, create a wall from (0,0) to (5,0), 3 metres high and 0.2 m thick.

**A room with a floor**
> On port 19753, create a closed 6 by 4 metre room of walls (3 m high), with a slab underneath it.

**A column**
> On port 19753, place a 0.4 by 0.4 m column, 3 m high, at (0,0).

**A beam (now with exact size)**
> On port 19753, create a beam from (0,0) to (6,0) at height 3 m, 0.2 m wide and 0.4 m deep.

**A staircase**
> On port 19753, create a straight stair along the line from (1,1) to (1,4), total height 3 m, flight width 1 m.

**A labelled zone (room area)**
> On port 19753, create a zone covering the rectangle (0,0)-(6,4) named "Living Room" number 01.

**A text note**
> On port 19753, add a text label saying "Concept - not for construction" at (3,2).

---

## Bigger builds (it works step by step)

You can ask for a whole layout. Be clear about the rooms and sizes; it will create things in the right order.

> On port 19753, build a small apartment in a 10 by 8 metre footprint:
> a slab over the whole footprint, perimeter walls 3 m high, and internal walls splitting it into a living room, two bedrooms and a bathroom. Add a column at each corner. Then add a zone for each room, named and numbered. Preview the walls and slab first, then build everything, and tell me what you created.

For **doors and windows**, make sure you did Step 4 of the setup (loaded the library), then:

> On port 19753, add a door to the entry wall and a window to each bedroom's outside wall.

---

## What it can do well

Walls · slabs · columns · beams (with exact cross-sections) · **stairs** · zones · meshes (terrain) · morphs (simple boxes) · text · labels · sections · doors & windows *(needs the library loaded)* · move/copy elements · property & classification setup.

It also **checks your geometry before building** — if you ask for something impossible (a zero-length wall, a crossed-over room outline), it tells you instead of making a mess.

## What it can't do (yet)

- **Roofs** — it will politely refuse (the roof tool isn't finished). Draw roofs manually.
- **Railings and curtain walls** — not available; draw manually.
- It builds **what you tell it** — it doesn't check building codes or whether a design is sensible. You're the architect; it's the fast pair of hands.

---

## Getting better results

- **Give coordinates and sizes.** "A 5×4 room at the origin" beats "a room."
- **Build in stages** for big jobs: structure first, then walls, then openings, then annotation. You can just say "now add…" in the same chat.
- **If a door/window fails,** it usually means the library isn't loaded — see setup Step 4.
- **If it created the wrong thing,** in ArchiCAD press **Ctrl+Z** (Undo) — a whole batch undoes in one step.
- **Ask it to confirm:** *"...then select everything you made so I can review it."* It will highlight the new elements in ArchiCAD.
- **If it says a command "doesn't exist"** after an update, fully restart Claude Desktop (tray icon → Quit, then reopen).

---

## Example conversation

> **You:** List my running ArchiCAD instances.
> **Claude:** Found one on port 19753 (Untitled project).
> **You:** On port 19753, preview a 5×4 m room of walls with a slab, then build it and confirm.
> **Claude:** Preview: 4 walls + 1 slab, footprint 0–5 × 0–4 m, looks valid. … Built and verified: 4 walls, 1 slab. Anything else?
> **You:** Now add a column at each corner and a straight stair in the middle.
> **Claude:** Done — 4 columns and 1 stair added.

---

*Have fun. If you hit a wall (the bad kind), screenshot the chat and send it to Adam.*
