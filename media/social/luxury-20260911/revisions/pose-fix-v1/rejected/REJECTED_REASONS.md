# pose-fix v1 — rejected attempts (pid 65)

Rule applied: any change to stone, engraving, shank thickness/cross-section, or pose ⇒ FAILED_QA.
Only the owner can declare APPROVED. Nothing here is approved or "accepted with flag".

## 65-A-posefix-v1-attempt1.png
- Pose/tilt: correctly off-axis (stone face visible), environment rich.
- FAIL: shank ribs render thinner/flatter than the reference's chunky round ribs.
- FAIL: an open band loop is shown in front, but the source photo hides the underside there (invented hidden part).
- FAIL: engraving glyph micro-shapes re-drawn (same words/design, not pixel-faithful).
- Also: stone tone slightly lighter than reference.

## 65-A-posefix-v1-attempt2.png
- FAIL: pose more upright (more "standing") than the reference tilt — owner's defect #1.
- FAIL: bezel teeth coarser / fewer than the reference sawtooth teeth.
- FAIL: ribs thinner; front loop invented.
- FAIL: engraving re-rendered and slightly stretched.

## 65-B-posefix-v1-attempt1.png
- Pose close, ribs close.
- FAIL: bezel tooth pattern and the bright bead rail beneath the bezel changed.
- FAIL: engraving glyph micro-shapes re-written (same words/design).

## 65-B-posefix-v1-attempt2.png  (best of the four)
- PASS on pose/attitude, tilt, oval stone proportions, sawtooth bezel teeth, bead rail,
  rib number/thickness, the open slot between ribs, contact shadow, environment.
- FAIL: engraving glyph micro-shapes re-rendered vs source (same words/design, not pixel-faithful).
- FAIL (minor): stone tone ~1 stop lighter than the reference.

## Conclusion of this revision run
The available image-editing model is prompted with the real reference + area-protection wording,
but it still re-renders the produced/written area of the ring instead of preserving it.
No accepted output was produced in this pilot. No composite/cutout fallback was used (per instruction).

## Requirement to pass
An editing model with hard region protection (masked inpaint that never regenerates the mask interior),
or a preservation mode that returns the source pixels unmodified outside the mask.
