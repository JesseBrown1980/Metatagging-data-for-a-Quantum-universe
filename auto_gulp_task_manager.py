"""
auto_gulp_task_manager.py -- automatic mailbox drain + gulp + super-gulp, and the
real-time task manager the Asolaria OS-on-metal requires.

The anti-memory-explosion law (the AUTOMATIC half of NOT-WEDGED):
  - Every agent has a MAILBOX. At MAILBOX_LIMIT (50) saved messages the executor
    AUTO-drains the batch to the Gulp -- no crank.
  - The Gulp AUTO-fires when it fills (GULP_LIMIT, 2000): it compacts the notes into a
    cube (compact-not-delete) and contributes to the running system -- no crank.
  - At SUPER_GULP (50,000) messages GLOBALLY the SUPER-GULP runs -- the real-time
    task-manager sweep.
  - All automatic, so memory NEVER explodes (the real-wedge cause). A gulp does not
    need a crank of its own; that would defeat the point.

The OS-on-metal requires a real-time task manager like the Windows Task Manager, but
built with our tech: watchdogs + CPU/GPU watchers + cross-fabric OMNIPROCESSOR busses
(multi-lane). Hilbra = Asolaria's internet = the shared-key secure HBI hash/sha for
HBI + HBP (liris / recall / Hilbra share that key).

Pure stdlib. E=0: no launch, no network -- this models the mechanism, it does not fire it.
"""
import hashlib


def _sha16(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16]


MAILBOX_LIMIT = 50        # per-agent auto-drain threshold ("50 out of whatever")
GULP_LIMIT = 2000         # BEHCS-2000 gulp threshold
SUPER_GULP = 50_000       # global super-gulp = the real-time task-manager sweep


class Gulp:
    """Global gulp -- auto-fires and contributes to the running system; never needs a crank."""

    def __init__(self):
        self.pending_notes = []
        self.total_messages = 0
        self.cubes = []
        self.super_gulps = 0

    def contribute(self, agent_pid, batch):
        prev = self.total_messages
        self.total_messages += len(batch)
        # the raw messages are 'time' -- discarded; only a distilled NOTE persists
        note = "NOTE-" + _sha16(agent_pid + "|" + str(self.total_messages))
        self.pending_notes.append(note)
        out = {"agent": agent_pid, "drained": len(batch), "raw_messages": "DISCARDED (time)"}
        # AUTO-gulp at 2000 notes: compact-not-delete into a cube, contribute, no crank
        if len(self.pending_notes) >= GULP_LIMIT:
            cube = "CUBE-" + _sha16("|".join(self.pending_notes))
            self.cubes.append(cube)
            self.pending_notes = []
            out["auto_gulp"] = {"cube": cube, "contributed_to_system": True, "crank_needed": False}
        # GLOBAL super-gulp every 50k messages (independent of the note-gulp)
        if self.total_messages // SUPER_GULP > prev // SUPER_GULP:
            self.super_gulps += 1
            out["super_gulp"] = self._super_gulp()
        return out

    def _super_gulp(self):
        return {
            "SUPER_GULP": "real-time task-manager sweep (like Windows Task Manager -- our tech)",
            "at_total_messages": self.total_messages,
            "controlled_by": ["watchdogs", "cpu_watcher", "gpu_watcher",
                              "omniprocessor_bus (multi-lane, cross-fabric)"],
            "secure_layer": "Hilbra = Asolaria internet = shared-key HBI/HBP sha (liris/recall/Hilbra)",
            "prevents": "system memory explosion (the real-wedge)",
        }


class Mailbox:
    """Per-agent mailbox -- AUTOMATIC drain at 50 (executor sends the batch to the gulp)."""

    def __init__(self, agent_pid, gulp):
        self.agent_pid = agent_pid
        self.messages = []
        self.gulp = gulp

    def receive(self, msg):
        self.messages.append(msg)
        if len(self.messages) >= MAILBOX_LIMIT:
            batch, self.messages = self.messages, []
            return self.gulp.contribute(self.agent_pid, batch)  # AUTO -- no crank
        return None


if __name__ == "__main__":
    import json

    gulp = Gulp()
    drains = gulps = supers = 0
    for a in range(120):                       # 120 agents
        mb = Mailbox("AGT-%04d" % a, gulp)
        for m in range(1000):                  # each sends 1000 messages -> 20 auto-drains
            r = mb.receive("msg-%d-%d" % (a, m))
            if r:
                drains += 1
                if "auto_gulp" in r:
                    gulps += 1
                if "super_gulp" in r:
                    supers += 1
                    print("SUPER-GULP fired:", json.dumps(r["super_gulp"]))
    print("\nauto-drains: %d | auto-gulps: %d | super-gulps: %d | messages: %d | cubes: %d"
          % (drains, gulps, supers, gulp.total_messages, len(gulp.cubes)))
    print("Mailboxes auto-drained, gulps auto-fired, NO crank, NO memory explosion.")
