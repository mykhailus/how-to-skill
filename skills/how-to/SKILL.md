---
name: how-to
description: "An instruction you can touch: for any \"how do I do X\" question, builds a single page – the order of steps on the left, a transparent ink drawing on the right that the reader works with their hands (drag, click, click fast). Steps tick themselves off as the reader performs them, and a \"done\" card appears at the end. Draws its own objects for every topic. Use when asked for an \"interactive instruction\", a \"how-to\", \"how to do X so I can play with it\", a \"hands-on explainer\" or a \"trainer page\". Input – a question or a ready-made instruction. Output – one html file that opens itself in the browser and one clickable link to it; with the --publish flag – a link to a claude.ai artifact."
argument-hint: "<how to … | text of a ready-made instruction> [--publish]"
version: 1.4
user-invocable: true
---

# how-to – an instruction you can touch

The result is one `html` file. The page holds only a title, the order of actions in 4–6 steps and a stage with a drawing. The drawing is transparent, ink only, no colour. The reader changes it by hand, and the labels on the objects answer at once.

`template.html` sits next to this file: the engine and a teaching sample, "how to brew a cup of tea".

## Launched without a topic

The skill was called with no text – build nothing. Answer with this one hint and wait:

```text
tell me what to explain: any "how do I …" question, or a ready-made instruction to bring to life.

for example:
– how to buy your first bitcoin
– how to set up two-factor authentication
– how to sharpen a knife
– how to read a food label

you can add who it is for and what the reader already has.
```

Any text after the call is a request. A topic or an action without the words "how to" ("pole vault?", "a pole", "change a tyre") reads as "how to do it": build the page. If the topic cannot be made out of the text at all, ask one clarifying question and carry on.

## Workflow

### 1. Gather the facts
The topic, the reader, what they should be able to do after the page. Take the steps from the user's materials or from verified sources. Do not invent numbers you do not have: turn the value into a handle and let the reader set their own.

### 2. Find the action
Answer in writing before any code:

1. **What does the reader do with their hands?** One to three kinds of gesture (there may be more handles): drag, lower, turn, click. Where real life takes effort or speed (boil, pump, whisk, crank), give a speed action: click the object fast until the gauge fills up within the given seconds.
2. **What changes because of it?** One or two things the reader cares about.
3. **What is the link?** A rule in a single function, `model(v)`.
4. **What should they see at the end?** The state of the drawing that the last step leads to.

A page where you can only flip through steps is an article. It does not need this skill.

### 3. Draw the objects of this topic
This is the main step. Make a vocabulary for the topic: 4–8 things the reader recognises at a glance. For tea it is a kettle, a cup, a tea bag, a timer. For buying bitcoin – a bank card, an exchange building, a coin, a wallet, a sheet with twelve words. For sharpening a knife – a knife, a whetstone, an angle.

Rules:

- **every object is drawn from bodies, anew for the topic.** The silhouette of a thing comes from `lathe` (anything round: crockery, coins, bottles, wheels), `extrude` (anything flat with a telling outline: a card, a house, a knife, an arrow, a person), `tube` (handles, wires, hoses, arcs), `plate` (a sign, a screen, a tag with text);
- **the handle is the thing itself.** People drag the tea bag, the coin, the knife, the switch. Abstract balls on rails and columns with caps mean the topic has not been drawn;
- **objects from the sample do not move into a new topic.** Take the structure of the code from `template.html` and invent the drawing from scratch. If your scene looks like a kettle with a cup or a row of columns – redraw it;
- **a value is shown with a body and hatching**: height, the level in a vessel, hatch density (`hatch: 1 | 2 | 3`), the number of objects. There is no colour in the drawing;
- no decoration: remove any object that means nothing and does not move.

Sketch each thing in words before the code: which bodies, what size, where it stands. The scene fits a strip 6–8 units wide and up to 3 high; the frame adjusts itself.

### 4. Write the steps
4–6 steps, each one a single action on the drawing, with a verb in the imperative. Two sentences per step. The last step is an action too: it brings the drawing to the result. The takeaway lives in the `finish` card; there is no action-free step at the end, otherwise the card never appears.

Every step with an action has a `done` condition: the reader did what was needed – the step gets a tick and the next one becomes active by itself. The condition checks the result through `model`, not the mere fact of a touch: "the bag is in the cup", not "the bag was touched". Steps go in the order in which they can be performed: the condition of the next step must not be true before the action of the previous one. All objects stand on the table from the start, so keep the order yourself:

- a value starts at "not set" (zero, the bottom of the scale), not at a plausible value – otherwise `done` is true from the outset;
- put the dependency into `model`: "paid" is true only when there is both an amount and a rate;
- send back a handle that was touched too early: in `release` remember the refusal in `s.mem`, in `update` ease the value back and show a label that says what is missing ("write the words down first");
- an object it is too early to touch can be hidden with `show` in the earlier steps.

The ending is visible twice. On the drawing: the result stays in place after the last action, and the label on the object names it ("tea is ready – just right") instead of going back to the hint. On the `finish` card: one or two sentences about what came out and what the reader did; it slides in by itself when the last step is done, with a "start over" button.

The voice of the page: the title and step names in lowercase; step text starts with a lowercase letter, with a capital after a full stop; en dash (–); no emoji. Everything the reader needs to know is in the step or in a label on an object.

### 5. Build the file
Copy `template.html` under a name for the topic (`how-to-buy-bitcoin.html`) into the folder where the user works. The file has three blocks, with comments marking the borders:

- `CONTENT` – replace entirely (together with `model`);
- `SCENE` – replace entirely;
- `ENGINE` and everything above it (styles, fonts) – do not change a line. If something is missing, write your own in `SCENE` with Three.js (`k.THREE`, `b.add(obj)`).

There is one `model(v)` function per page: both the placement of objects and the labels call it. That way the numbers never drift from the picture.

### 6. Open the page and hand over the link
First open the finished file yourself in the user's regular browser – with one shell command, no built-in browser and no local server:

- Windows (PowerShell): `Start-Process "C:\work\how-to-buy-bitcoin.html"`
- macOS: `open "/path/how-to-buy-bitcoin.html"`
- Linux: `xdg-open "/path/how-to-buy-bitcoin.html"`

A built-in app browser shows local files without scripts and the page stays blank there; that is why the system browser is used.

Then the answer to the user – one clickable link to the file and nothing else:

```text
[how to buy bitcoin](file:///C:/work/how-to-buy-bitcoin.html)
```

The address uses `file:///`, forward slashes and `%20` for spaces. No retelling, no explanations.

The page needs the internet for fonts and the graphics library.

### 7. Publishing – only with the `--publish` flag
The user asked to publish or share the page – put it out as an artifact, and the link opens anywhere:

1. `python -I -X utf8 to_artifact.py <page.html>` (the script sits next to this file) – strips the html/head/body wrapper and puts the instruction name into `<title>`; the result lands next to the page as `<page>.artifact.html`.
2. Publish that file with the Artifact tool: `icon: "guide"`, and in `description` one sentence about what people do on the page.
3. The answer is one link to the artifact: `[how to buy bitcoin](https://claude.ai/artifact/…)`. Do not open the local file in the browser in this case.

An artifact is private: only its owner sees it until they share it through Share on the page. If the page is meant for other people, add one line about that under the link. No Artifact tool in the session – say so in one line and hand over the local link as in step 6.

## CONTENT

```js
const model = v => ({ /* everything that depends on the reader's actions */ });

const CONTENT = {
  kicker: 'instruction',
  title: 'how to …',              // lowercase
  lead: 'one or two lines: what comes out and what to do on the stage.',
  hint: 'click …, drag …',        // a hint in the corner of the stage
  finish: '… is ready. You finished the instruction: …',   // the card after the last step, next to the "start over" button
  steps: [{ title, text,
            done: s => model(s.raw).ok,   // the action is done – the step is ticked, the next one turns on
            focus: ['id'],        // these parts are drawn bolder
            show:  ['id'],        // optional: show only these
            set:   { id: 5 } }],  // optional: set values on entering the step
  controls: [                     // model values; not drawn on the page
    { id, type: 'range',  min, max, step, value },   // moved by a handle
    { id, type: 'toggle', value: 0 },                // switched by a click
    { id, type: 'choice', value },
  ],
};
```

## SCENE

```js
function SCENE(k) {
  const p = k.part('id', { pos: [x, 0, z], rot, label: 'label' }, b => {
    b.lathe({ profile: [[r, y], ...] });               // a body of revolution around the vertical axis
    b.extrude({ shape: [[x, y], ...], depth });        // an outline in the XY plane extruded along Z
    b.tube({ path: [[x, y, z], ...], r });             // a tube along a curve
    b.box({ size: [x, y, z] });  b.cyl({ r, h });  b.cone({ r, h });  b.sphere({ r });  b.torus({ r, tube, arc });
    b.line([[x, y, z], ...], { dashed, width });       // an ink stroke
    b.ring({ r });                                     // a circle in the horizontal plane
    b.plate({ text: 'exchange', w, h });               // a plate with text
  });
  // every body takes: pos, rot (degrees), hatch: 1 | 2 | 3, lines: false, rim: false

  k.sheet('id', { w, h, lines: 6, pos, rot });         // a sheet with lines
  k.jar('id',   { r, h, pos });                        // a jar gauge: part.level = 0..1
  k.flow('id',  [[x, y, z], ...], { speed, dots });    // a dashed line with running dots
  k.handle('id', { value: 'ctlId', path: [[x, y, z], ...] });   // the part travels along the path and changes a value

  return {
    update(s) {},        // every frame: place parts and labels according to model
    tap(id, s) {},       // a part was clicked
    release(id, s) {},   // a handle was released: start a flight, a throw, a send
    step(i, s) {}, reset(s) {},
  };
}
```

State `s`: `s.raw` – exact values for `model` and labels, `s.v` – smoothed values for fluid motion, `s.set(id, x)`, `s.part(id)`, `s.t`, `s.dt`, `s.dragging`, `s.mem` – memory between frames.

A label stands above the object, centred; `labelDy` in the part options moves its height (`k.part('id', { label, labelDy: 0.4 }, …)`). The engine keeps labels inside the stage and spreads overlapping ones vertically; still, write short labels, two to four words.

A part has: `part.on` (show or hide; the part rises from the table by itself), `part.pivot.position.x/z` and `part.inner.position.y` (move), `part.inner.rotation`, `part.inner.scale.y` (grow upwards: put the base of the body at zero), `part.labelText` (the label, `\n` breaks the line), `part.level` (a jar).

A speed action is assembled in `SCENE`: `tap` adds to a value in `s.mem`, `update` decreases it by `s.dt` and watches the deadline by `s.t`; reached the end – `s.set('done', 1)`, time is up – reset and a "try again" label. Check success inside `tap`, before the cooling in `update` eats the last click. Progress shows on the object itself (growing hatching), the seconds left – in the label. An attempt is passable with an ordinary hand: 2–3 clicks per second. The sample is the kettle in `template.html`.

The drawing is transparent, so the smallest part under the pointer wins, not the one nearest to the viewer: a swimmer can be clicked through the pool, a coin through the wallet. Keep a clickable part smaller than whatever it stands inside.

A handle's path is drawn as a dashed line by itself, and the handle pulses until it is touched. A handle can follow a polyline or a circle: give the path as points. Compute physical motion in `update` by `s.dt`, keep it in `s.mem`, start it from `release`.

## What not to do

- a page where you can only flip through steps;
- a step with an action and no `done` condition;
- a scene made of the sample's objects or of faceless cubes, balls and columns;
- colour in the drawing, sliders, quizzes, glossaries, footnotes, any blocks other than the steps and the stage;
- edits to `ENGINE` and the styles;
- numbers computed outside `model`, and invented data presented as fact;
- more than 8 objects and 6 steps;
- an answer longer than one link.
