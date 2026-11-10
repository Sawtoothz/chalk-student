---
source: xu-fastlio2
unit: 1
stage: cards
---

# Practical implementation: from the paper to a running LIO

The goal is not to re-create FAST-LIO2. It is to own every equation in C1–C6 by building a small LIO that works on
real data, then to read the authors' code with that in hand. Two deliverables, in this order:

1. **`fastlio_mini/` — a NumPy prototype** (~600 lines) that runs offline on one recorded sequence at 1–3 Hz. Correctness first.
2. **`fastlio_cpp/` — a C++17 port** of the same code with Eigen and the real ikd-Tree, running at sensor rate on the tracked robot's Livox/Ouster + IMU. Speed second.

## Step order (each step has a check that must pass before the next)

| # | build | check (oracle) | card |
| --- | --- | --- | --- |
| 1 | `manifold.py`: `so3_exp/log`, `s2_boxplus/boxminus`, `boxplus/boxminus`, `boxplus_jacobian` | `boxminus(boxplus(x,d), x) ≈ d` for random `d` (1e-9); finite-difference check of `boxplus_jacobian` with `just fd` | C1 |
| 2 | `propagate.py`: `f`, `F_dx`, `F_w`, `predict` | `F_dx` vs finite differences of `boxminus(predict(boxplus(x,d)), predict(x))`; on a 10 s synthetic IMU stream with known truth, pose error grows like a random walk, no bias | C2 |
| 3 | `undistort.py` | synthetic: a plane scanned while rotating at 1 rad/s; after undistortion the points fit one plane with residual < 1 mm (before: tens of cm) | C3 |
| 4 | `measure.py`: `fit_plane`, `residual_and_H` | `H` vs finite differences of `z` over `boxplus` (1e-6); plane fit recovers a known normal under 1 cm noise | C4 |
| 5 | `update.py`: `iterated_update`; `VoxelMap` | **gain identity test (T2)**: on random `H` (2000×23) the information-form `K` equals the textbook `K` to 1e-8; synthetic room with 6 planes: converges from a 0.3 m / 10° initial error in ≤ 4 iterations | C5, C6 |
| 6 | `run_offline.py`: the loop over one sequence; trajectory, map, timings to `results/` | ATE against the sequence's ground truth; drift < 1 % of path length on a 100 m loop; mean iteration count and ms/scan logged | all |
| 7 | C++ port, same file layout, same tests via pybind11 or a tiny CSV harness; swap `VoxelMap` for `ikd-Tree` | identical numbers to the prototype on the same sequence (to 1e-6 in pose); ≥ 10 Hz on the robot's compute | C6 |

Numbers in the check column are targets to be measured, not results — this package records a number only after a run.

## Data

- Start with the authors' own recordings linked from the FAST_LIO README (Livox Avia indoor/outdoor rosbags); they match the shipped `config/avia.yaml`, so a prototype that diverges there has a bug, not a data problem.
- Then one sequence from the robot: 60 s, a loop, start and end at the same marked spot (gives a loop-closure error without a mocap).
- Extrinsics ${}^I\mathbf{T}_L$: take them from the mount drawing first; turn on `estimate_extrinsic` only after step 6 passes with them fixed.

## What to copy from the paper, what to borrow from the code, what to leave out

| keep | reason |
| --- | --- |
| the state layout and $\mathbb{S}^2$ gravity | otherwise gravity wanders and the filter looks healthy while it drifts |
| the information-form gain | the only reason thousands of points per scan are affordable |
| backward propagation per point | the single biggest accuracy gain in a direct method |
| plane acceptance 0.1 m and the $s > 0.9$ weight | cheap robustness; found in the code, not the paper |
| re-search neighbours only when the previous step was small | halves the per-scan time; found in the code (`converge` flag) |

| leave out of the prototype | reason |
| --- | --- |
| ikd-Tree | validate the estimator against a plain k-d tree first; the tree is a speed feature |
| multi-threading, the moving local map (`lasermap_fov_segment`) | not needed under 200 m |
| ROS | read the bag with `rosbags` (pure Python) in the prototype; the C++ port can be a ROS 2 node later |

## Pitfalls the code warns about and the paper does not

- Per-point timestamps live in `curvature` in **milliseconds** in the authors' pipeline; ours are seconds from scan start. Convert once, at load.
- The undistortion uses the scan-end extrinsic and the authors mark the line `// not accurate!` — the error is second order in the IMU–LiDAR lever arm; measure it in step 3 by comparing against the exact per-point transform.
- Gravity initialisation: the code averages the first ~20 IMU samples standing still (`IMU_init`, `src/IMU_Processing.hpp:159`). The prototype should refuse to start if the vehicle moves during that window (|acc| − 9.81 > 0.2 m/s²).
- `LASER_POINT_COV` (0.001 by default) is a single scalar for every point: $\mathbf{R} = r\mathbf{I}$. The NIS test in step 6 tells you whether that is honest for your LiDAR; if NIS ≫ 1 raise $r$ before touching anything else.
- Iteration limit 4 and the per-state convergence `limit` (`epsi`) are tuning, not theory; log the iteration count per scan.

## Licence note

FAST_LIO, ikd-Tree and IKFoM are GPL-2.0. Our prototype and port are written from the equations (clean-room); the
links in `translate.md` are for reading alongside. If any file is ever copied rather than rewritten, that file and
everything that links it falls under GPL-2.0 — decide before step 7 whether that is acceptable for the robot code.
