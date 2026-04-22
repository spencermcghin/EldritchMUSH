# Playtest run: quest-crows

- **Target:** uat (https://uat.eldritchmush.com)
- **Character:** Quest Tester
- **Start:** 2026-04-22T02:43:06.546Z
- **Duration:** 21.6s
- **Result:** ✅ PASS

## Screenshots
- `uat-quest-crows-00-reset.png`
- `uat-quest-crows-01-post-load.png`
- `uat-quest-crows-02a-charsel-empty.png`
- `uat-quest-crows-02b-charcreate-modal.png`
- `uat-quest-crows-98-journal-final.png`
- `uat-quest-crows-99-failure.png`
- `uat-quest-crows-99-final-report.png`
- `uat-quest-crows-q10-rescue-blacksmith-accepted.png`
- `uat-quest-crows-q10-rescue-blacksmith-completed.png`
- `uat-quest-crows-q10-rescue-blacksmith-detail.png`
- `uat-quest-crows-q10-rescue-blacksmith-room.png`
- `uat-quest-crows-q11-rescue-alchemist-accepted.png`
- `uat-quest-crows-q11-rescue-alchemist-completed.png`
- `uat-quest-crows-q11-rescue-alchemist-detail.png`
- `uat-quest-crows-q12-rescue-artificer-accepted.png`
- `uat-quest-crows-q12-rescue-artificer-completed.png`
- `uat-quest-crows-q12-rescue-artificer-detail.png`

## Game feed (server [qtest]/[test] lines)
```
sg(f&quot;[qtest] reset. silver={me.db.silver or 0}&quot;)"], {"type": "py_input"}]
"text", ["[qtest] reset. silver=0"], {}]
msg(&quot;[qtest] rescue_alchemist injected as active&quot;)"], {"type": "py_input"}]
"text", ["[qtest] rescue_alchemist injected as active"], {}]
msg(&quot;[qtest] rescue_artificer injected as active&quot;)"], {"type": "py_input"}]
"text", ["[qtest] rescue_artificer injected as active"], {}]
sg(f&quot;[qtest] statuses: {statuses}&quot;); me.msg(f&quot;[qtest] silver: {start_s} -&gt; {me.db.silver or 0} (\u0394{(me.db.silver or 0) - start_s})&quot;); me.msg(f&quot;[qtest] new inventory: {new_inv}&quot;); me.msg(f&quot;[qtest] reagent deltas: {delta_r}&quot;)"], {"type": "py_input"}]
"text", ["[qtest] statuses: {'rescue_alchemist': 'active', 'rescue_artificer': 'active'}"], {}]
"text", ["[qtest] silver: 0 -&gt; 0 (\u03940)"], {}]
"text", ["[qtest] new inventory: []"], {}]
"text", ["[qtest] reagent deltas: {}"], {}]
```

## Browser console errors
_(none)_
