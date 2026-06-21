# Futurelock
Lock a message to your future self. It's sealed on 0G the moment you hit send — no peeking until your unlock date arrives.
# ⏳ Futurelock

You write something. You pick a date. You hit seal.

That's it — the message is gone from your screen and locked away on 
0G's decentralized storage. Not "locked" in the way a folder password 
is locked, where anyone determined enough gets in anyway. Actually 
gone from your reach until the date you chose, because the only copy 
that matters isn't on your computer anymore.

A submission for the [0G Zero Cup](https://0g.ai/arena/zero-cup).

---

**The problem with every other "time capsule" app:** they're all 
theater. The data sits right there on disk the whole time. Anyone with 
five minutes and a text editor can open the file, change the unlock 
date, or just read it early. The "lock" is a UI suggestion, not a 
real one.

**What changes with 0G:** the message physically leaves your machine 
the second you seal it. There's nothing local to crack open, no date 
field to edit, no file to peek at. Uninstall the app, format your 
drive, buy a new laptop — the capsule is still sitting on 0G exactly 
where you left it, waiting for the date you picked.

---

### Try it on yourself, or someone else

- Write a prediction before a big event, seal it for a month out
- Leave a note for your future self before a decision you're nervous 
  about
- Set something to unlock on a birthday, an anniversary, a deadline
- Commit to a goal in writing, in a way you genuinely can't go back 
  and quietly edit later

### Under the hood

Every "Seal" press triggers a real transaction to 0G's storage 
network and comes back with a permanent root hash — proof, if you 
ever needed it, of exactly when that capsule was sealed.

---

## Setting it up (judges / developers)

You'll need **Node.js** alongside the Windows build.

Grab Futurelock.exe + sidecar.zip from Releases
Unzip sidecar.zip next to the .exe
Install Node.js (nodejs.org) if you don't have it
cd sidecar && npm install
Copy env.example → .env, drop in a testnet wallet key

(free test tokens: faucet.0g.ai)
Run Futurelock.exe — write, pick a date, seal it
