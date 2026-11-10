# T5 — Robot application: should the tracked robot's VO initializer fit a homography or a fundamental matrix, and where does the metre come from?

Every monocular VO or VIO front end starts with two frames: from matches alone it must decide whether
it has enough parallax to triangulate, recover the relative pose, and set the scale. This chapter tells
you why that is hard. A camera that only rotates, or a scene that is only floor, gives a homography,
not an F (Fig. 1.1, p. 8; transfer by H, p. 16). A reconstruction from images is projective, or a similarity at best once
calibrated (pp. 11, 17), so the metre has to come from somewhere else.

## Setup

The tracked robot of `models.py`: K as in the lecture, camera h = 0.55 m above the floor, pitched 15°
down, mounted ahead of the turning centre. A warehouse aisle: textured floor and boxes 3–11 m away.
`python3 -m exercises.T5_sim` (from the package dir) regenerates `data/` (already shipped):

| File | What you know |
| --- | --- |
| `t5_pan.npz`, `t5_floor_only.npz`, `t5_drive_turn.npz`, `t5_skid_turn.npz`, `t5_creep.npz`, `t5_drive_far.npz` | the pair's name, nothing else about the motion |
| `t5_drive_turn_outliers.npz` | the same pair with some matches replaced by junk |

Each file holds `u1`, `u2` (N×2 matched pixels, noisy), `floor` (N bools from the robot's floor
segmenter), `K`, and `h`. The motion and the noise level are hidden in `T5_sim.py`. Do not open it.

Tools: your T3 functions; `models.fit_homography`, `models.fit_fundamental` (normalized, ch. 4 and ch. 11)
and `models.essential_candidates` (§9.6). They are given; you write them in later packages.

## Tasks

1. **Fit both.** For every pair, fit H and F to all matches. Report the RMS transfer error of H
   (pixels, ‖H x − x′‖ in image 2) and the RMS epipolar distance of F (your `epipolar_distance_px`).
   Estimate the detector noise σ from the residuals and say how.
2. **Decide.** Write a rule that classifies each pair as "H: rotation or plane, do not triangulate" or
   "F: enough parallax". Justify its threshold from what noise alone would give. Before looking at
   anything else, write down which motion you think each pair is.
3. **Pose and scale.** For the pairs you call F: form E = KᵀFK, pick the right one of the four
   `essential_candidates` by cheirality (your `triangulate` and `depth`), and report the rotation angle.
   The translation has unit length: that is the similarity ambiguity (p. 11). Recover metres from the
   floor. Triangulate the floor points, fit a plane, and compare camera 1's height above it with h = 0.55 m.
   Report the camera's baseline in metres. Then do it again with only floor points whose two rays meet
   at more than 1° (your `ray_angle`), and explain the difference.
4. **Stress.** For every pair, refit F on 40 random halves of the matches and report the spread of the
   recovered translation direction (RMS angle to the mean, degrees). Which pairs give a pose you would
   accept? What does the skid turn teach you about where the camera is mounted?
5. **Outliers.** Run task 1 on `t5_drive_turn_outliers.npz`. Then write a RANSAC around
   `fit_fundamental` (8-point samples, threshold in pixels from your σ). Report the inlier count, the
   residual, the translation direction and the baseline after RANSAC.
6. **Write-up (half a page).** The initializer rule you would ship on the tracked robot and on the drone:
   when to fit H, when to fit F, when to wait for more motion. Where the metre comes from on each robot
   (camera height, wheel odometry, IMU). One plot you would put on the debug dashboard.

## Deliverables

- `T5_report.md` with a table of the numbers per pair and the plots (`viz.py.style`).
- `T5_init.yaml` with your decision rule, thresholds and RANSAC settings.

## Self-check

`solutions/T5.md` gives the hidden motions, the noise level and reference numbers from
`solutions/T5_reference.py` run on the shipped data. Compare only after you have written the report.
