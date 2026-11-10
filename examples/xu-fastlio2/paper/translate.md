---
source: xu-fastlio2
unit: 1
stage: cards
code_refs: code_refs.json
---

# Equation → code cards

Every **In the original code** block below cites `path:line` taken from `code_refs.json` (repository, commit, licence
recorded there). Line numbers are for that commit only. Our snippets are a clean-room NumPy translation of the
equations, written to be read next to the original, not copied from it.

---

## C1 · The state lives on a manifold; errors live in its tangent space

**Equation.** The state and its error:

$$\mathbf{x} = [\,^G\mathbf{R}_I,\ ^G\mathbf{p}_I,\ ^G\mathbf{v}_I,\ \mathbf{b}_\omega,\ \mathbf{b}_a,\ ^G\mathbf{g},\ ^I\mathbf{R}_L,\ ^I\mathbf{p}_L\,]
\in SO(3)\times\mathbb{R}^{15}\times\mathbb{S}^2\times SO(3)\times\mathbb{R}^3,\qquad
\mathbf{x} = \hat{\mathbf{x}} \boxplus \delta\mathbf{x},\ \ \delta\mathbf{x}\in\mathbb{R}^{23}.$$

For a rotation $\mathbf{R}\boxplus\boldsymbol\theta = \mathbf{R}\,\mathrm{Exp}(\boldsymbol\theta)$ and $\mathbf{R}_1\boxminus\mathbf{R}_2 = \mathrm{Log}(\mathbf{R}_2^T\mathbf{R}_1)$; for a vector ⊞ is $+$; for gravity on $\mathbb{S}^2$ the increment is 2-dimensional.

**Why it matters.** 24 numbers stored, 23 corrected. The filter never adds to a rotation matrix; it composes. Gravity has fixed norm, so a 3-vector would carry a direction the data cannot observe and the covariance would go singular along it.

**Code (ours).**

```python
def boxplus(x, dx):                       # x: dict of parts, dx: (23,)
    return {
        "R":  x["R"] @ so3_exp(dx[0:3]),  "p": x["p"] + dx[3:6],  "v": x["v"] + dx[6:9],
        "bg": x["bg"] + dx[9:12],         "ba": x["ba"] + dx[12:15],
        "g":  s2_boxplus(x["g"], dx[15:17]),                      # 2-dof update on the sphere
        "R_IL": x["R_IL"] @ so3_exp(dx[17:20]), "p_IL": x["p_IL"] + dx[20:23],
    }

def boxminus(x, y):                       # x ⊟ y -> (23,)
    return np.concatenate([so3_log(y["R"].T @ x["R"]), x["p"]-y["p"], x["v"]-y["v"], x["bg"]-y["bg"], x["ba"]-y["ba"],
                           s2_boxminus(x["g"], y["g"]), so3_log(y["R_IL"].T @ x["R_IL"]), x["p_IL"]-y["p_IL"]])
```

**Trick.** Store `g` as a unit vector and keep the 2-dof tangent basis with it (two orthonormal vectors in the tangent plane). Recompute the basis after every update, or the second-order terms bite within a few hundred steps.

**In the original code.** The state type is declared with the IKFoM `MTK_BUILD_MANIFOLD` macro — `include/use-ikfom.hpp:12` (`MTK_BUILD_MANIFOLD(state_ikfom, …` with `vect3 pos`, `SO3 rot`, `S2 grav` …), and ⊞/⊟ are generated from it; the filter calls them at `include/IKFoM_toolkit/esekfom/esekfom.hpp:1817` (`x_.boxplus(dx_)`) and `:421` (`x_.boxminus(dx, x_propagated)`). The $\mathbb{S}^2$ tangent maps are `S2_Mx` / `S2_Nx_yy` at `esekfom.hpp:1689-1691`.
https://github.com/hku-mars/FAST_LIO/blob/7cc4175de6f8ba2edf34bab02a42195b141027e9/include/use-ikfom.hpp#L12

---

## C2 · Forward propagation: the IMU drives the nominal state and the covariance

**Equation (Eq. 2–6).** With IMU sample $(\boldsymbol\omega_m, \mathbf{a}_m)$ over $\Delta t$:

$$\hat{\mathbf{x}}_{i+1} = \hat{\mathbf{x}}_i \boxplus \big(\Delta t\, \mathbf{f}(\hat{\mathbf{x}}_i, \mathbf{u}_i, \mathbf{0})\big),\qquad
\hat{\mathbf{P}}_{i+1} = \mathbf{F}_{\delta\mathbf{x}} \hat{\mathbf{P}}_i \mathbf{F}_{\delta\mathbf{x}}^T + \mathbf{F}_{\mathbf{w}}\mathbf{Q}\mathbf{F}_{\mathbf{w}}^T$$

with $\mathbf{f} = [\boldsymbol\omega_m - \mathbf{b}_\omega,\ \mathbf{v},\ \mathbf{R}(\mathbf{a}_m-\mathbf{b}_a)+\mathbf{g},\ \mathbf{0},\ \mathbf{0},\ \mathbf{0},\ \mathbf{0},\ \mathbf{0}]$.

**Code (ours).**

```python
def f(x, u):                               # 24-dim rate (3 rot, 3 pos, 3 vel, rest zero)
    w = u.gyro - x["bg"]; a = x["R"] @ (u.acc - x["ba"]) + x["g"]
    return w, x["v"], a

def F_dx(x, u, dt):                        # 23x23, only the non-identity blocks
    F = np.eye(23)
    F[0:3, 0:3]   = so3_exp(-(u.gyro - x["bg"]) * dt)        # rotation error transport
    F[0:3, 9:12]  = -np.eye(3) * dt                           # d rot / d bg
    F[3:6, 6:9]   = np.eye(3) * dt                            # d pos / d vel
    F[6:9, 0:3]   = -x["R"] @ skew(u.acc - x["ba"]) * dt      # d vel / d rot
    F[6:9, 12:15] = -x["R"] * dt                              # d vel / d ba
    F[6:9, 15:17] = s2_basis(x["g"]) * dt                     # d vel / d g  (3x2)
    return F
```

**Trick.** The paper writes $\mathbf{F}$ as $\mathbf{I} + \Delta t\,\partial\mathbf{f}/\partial\delta\mathbf{x}$; the code computes $\partial\mathbf{f}/\partial\delta\mathbf{x}$ once (`df_dx`) and lets the toolkit do the $\mathbf{I} + \Delta t(\cdot)$. Keep that split: it makes `fd_check` of `df_dx` a 24×23 finite-difference test with no $\Delta t$ in it.

**In the original code.** `get_f` — `include/use-ikfom.hpp:47`; `df_dx` — `:61` (note `cov.block<3,2>(12,21) = grav_matrix`, the $\mathbb{S}^2$ column pair); `df_dw` — `:80`. The propagation itself, including the $\mathbf{F}\mathbf{P}\mathbf{F}^T + \mathbf{F}_w\mathbf{Q}\mathbf{F}_w^T$ line, is `esekfom.hpp:275` (`predict`) with the covariance line at `:378`. Called per IMU sample from `src/IMU_Processing.hpp` inside `UndistortPcl` (`:216`).
https://github.com/hku-mars/FAST_LIO/blob/7cc4175de6f8ba2edf34bab02a42195b141027e9/include/use-ikfom.hpp#L47-L80

---

## C3 · Backward propagation: undistort every point to the scan-end frame

**Equation (Eq. 7–8).** Inside one scan, for a point measured at $\rho_j$ in LiDAR frame $L_j$, with IMU poses integrated backwards from the scan end $t_k$:

$$^{L_k}\mathbf{p}_{f_j} = {}^{I}\mathbf{T}_L^{-1}\, {}^{I_k}\check{\mathbf{T}}_{I_j}\, {}^{I}\mathbf{T}_L\, {}^{L_j}\mathbf{p}_{f_j},\qquad
{}^{I_k}\check{\mathbf{T}}_{I_j} = \big({}^{G}\hat{\mathbf{T}}_{I_k}\big)^{-1}\, {}^{G}\check{\mathbf{T}}_{I_j}.$$

**Why it matters.** A 10 Hz spinning LiDAR moving at 1 m/s smears a scan by 10 cm; a 1 rad/s turn by 6° at 1 m. Direct registration of raw points without this step matches smeared geometry to a crisp map and the filter converges to a wrong pose confidently.

**Code (ours).**

```python
def undistort(points, t, imu_poses, x_end, R_IL, p_IL):
    """points: (N,3) in LiDAR frame at times t (seconds from scan start); imu_poses: list of (t_i, R_i, p_i, v_i, a_i)
    integrated forward over the scan; x_end: state at scan end. Returns points in the scan-end LiDAR frame."""
    out = np.empty_like(points)
    R_e, p_e = x_end["R"], x_end["p"]
    for j, (pt, tj) in enumerate(zip(points, t)):
        i = bisect(imu_poses, tj)                      # last IMU pose at or before tj
        ti, R_i, p_i, v_i, a_i = imu_poses[i]; dt = tj - ti
        R_j = R_i @ so3_exp(w_i * dt)                  # w_i: gyro of that interval
        p_j = p_i + v_i * dt + 0.5 * a_i * dt * dt     # second-order position inside the interval
        pw  = R_j @ (R_IL @ pt + p_IL) + p_j           # point in G
        out[j] = R_IL.T @ (R_e.T @ (pw - p_e) - p_IL)  # back to LiDAR frame at scan end
    return out
```

**Trick.** Iterate points in *descending* time while walking the IMU pose list backwards, so each pose lookup is $O(1)$ instead of a bisect; that is the whole reason the paper calls it *backward* propagation. Also: the per-point timestamp is stored in the PCL `curvature` field in milliseconds (`/1000` in the code) — a classic source of unit bugs when porting.

**In the original code.** `src/IMU_Processing.hpp:307` (comment "undistort each lidar point (backward propagation)") through `:345`: `R_i(R_imu * Exp(angvel_avr, dt))`, `T_ei(pos_imu + vel_imu*dt + 0.5*acc_imu*dt*dt - imu_state.pos)` and the `P_compensate` line, which carries the authors' own comment `// not accurate!` (the rotation uses the end-of-scan extrinsic without re-estimating it). Forward IMU integration that produces `IMUpose` is the loop just above it in `UndistortPcl` (`:216`).
https://github.com/hku-mars/FAST_LIO/blob/7cc4175de6f8ba2edf34bab02a42195b141027e9/src/IMU_Processing.hpp#L307-L345

---

## C4 · The measurement: point-to-plane distance and its Jacobian

**Equation (Eq. 9–12).** For point $j$ with the plane $(\mathbf{u}_j, \mathbf{q}_j)$ fitted to its 5 nearest map points:

$$z_j = \mathbf{u}_j^T\big({}^{G}\hat{\mathbf{T}}_{I_k}\, {}^{I}\mathbf{T}_L\, {}^{L_k}\mathbf{p}_{f_j} - \mathbf{q}_j\big),\qquad
\mathbf{H}_j = \frac{\partial z_j}{\partial \delta\mathbf{x}} = \big[\ \mathbf{u}_j^T,\ \ -\mathbf{u}_j^T\,{}^{G}\hat{\mathbf{R}}_{I}\,\lfloor {}^{I}\mathbf{p}_{f_j}\rfloor_\times,\ \ \mathbf{0}_{1\times 9},\ \ (\text{extrinsic cols})\ \big]$$

where ${}^{I}\mathbf{p}_{f_j} = {}^{I}\mathbf{R}_L\,{}^{L}\mathbf{p}_{f_j} + {}^{I}\mathbf{p}_L$, and the plane is accepted only if all 5 points lie within 0.1 m of it.

**Code (ours).**

```python
def fit_plane(P):                         # P: (5,3) -> unit normal n, offset d with n·x + d = 0, or None
    n = np.linalg.lstsq(P, -np.ones(5), rcond=None)[0]
    s = np.linalg.norm(n); n, d = n / s, 1.0 / s
    return (n, d) if np.all(np.abs(P @ n + d) < 0.1) else None

def residual_and_H(x, p_L, n, d, estimate_extrinsic=False):
    p_I = x["R_IL"] @ p_L + x["p_IL"]
    p_G = x["R"] @ p_I + x["p"]
    z = n @ p_G + d                          # signed distance (the measurement is -z, h(x)=z)
    H = np.zeros(23)
    H[3:6] = n                               # d z / d p
    H[0:3] = -n @ x["R"] @ skew(p_I)         # d z / d theta  (rotation error on the right)
    if estimate_extrinsic:
        H[17:20] = -n @ x["R"] @ x["R_IL"] @ skew(p_L)
        H[20:23] = n @ x["R"]
    return z, H
```

**Trick.** The paper's weight $s = 1 - 0.9\,|z|/\sqrt{\|\mathbf{p}\|}$ with $s>0.9$ is a crude robust kernel: far points tolerate larger residuals. Keep it; dropping it is the first thing that makes a direct method diverge in long corridors. Note the residual is written as `h = -pd2` and the Jacobian row begins with the normal — the convention matches ours once you flip the sign consistently.

**In the original code.** `src/laserMapping.cpp:638` `h_share_model`: transform to world (`:656-657`), 5-NN in the ikd-Tree (`:670`), plane fit `esti_plane` (`:678`, definition `include/common_lib.h:226`), the weight `s` (`:681`), the $\mathbf{H}$ row assembly (`:737-748`, 12 columns when `extrinsic_est_en`, 6 otherwise) and `ekfom_data.h(i) = -norm_p.intensity` (`:751`).
https://github.com/hku-mars/FAST_LIO/blob/7cc4175de6f8ba2edf34bab02a42195b141027e9/src/laserMapping.cpp#L638-L752

---

## C5 · The iterated update with the gain in information form

**Equation (Eq. 18–20).** At iteration $\kappa$, with $\mathbf{J}^\kappa$ the ⊞-Jacobian relating the current error to the propagated one, $\mathbf{P} = \mathbf{J}^{-1}\hat{\mathbf{P}}\mathbf{J}^{-T}$:

$$\mathbf{K} = \big(\mathbf{H}^T\mathbf{R}^{-1}\mathbf{H} + \mathbf{P}^{-1}\big)^{-1}\mathbf{H}^T\mathbf{R}^{-1},\qquad
\hat{\mathbf{x}}^{\kappa+1} = \hat{\mathbf{x}}^{\kappa} \boxplus \Big(-\mathbf{K}\mathbf{z}^{\kappa} - (\mathbf{I}-\mathbf{K}\mathbf{H})\,\mathbf{J}^{-1}\big(\hat{\mathbf{x}}^{\kappa}\boxminus\hat{\mathbf{x}}\big)\Big)$$

and on convergence $\bar{\mathbf{P}} = (\mathbf{I}-\mathbf{K}\mathbf{H})\mathbf{P}$.

**Why it matters.** $\mathbf{H}$ is $m\times 23$ with $m$ in the thousands. The textbook gain inverts $m\times m$; this one inverts $23\times 23$. Same gain algebraically (matrix inversion lemma, exercise T2), 10³–10⁴× less work. With $\mathbf{R}=r\mathbf{I}$ even $\mathbf{R}^{-1}$ is a scalar.

**Code (ours).**

```python
def iterated_update(x_prop, P_prop, scan, mapkd, r=0.001, iters=4, tol=(1e-3, 1e-3)):
    x = dict(x_prop)
    for k in range(iters):
        dx  = boxminus(x, x_prop)                     # error w.r.t. propagated state
        J   = boxplus_jacobian(x_prop, dx)            # 23x23, identity except the SO(3)/S2 blocks
        P   = np.linalg.solve(J, np.linalg.solve(J, P_prop).T).T    # J^{-1} P J^{-T}
        zs, Hs = [], []
        for p_L in scan:                              # residuals against the current x
            nb = mapkd.query(world(x, p_L), 5)
            pl = fit_plane(nb)
            if pl is None: continue
            z, H = residual_and_H(x, p_L, *pl); zs.append(z); Hs.append(H)
        z, H = np.array(zs), np.array(Hs)
        HtRH = H.T @ H / r                            # 23x23
        Pinv = np.linalg.inv(P)
        K    = np.linalg.solve(HtRH + Pinv, H.T / r)  # (H^T R^-1 H + P^-1)^-1 H^T R^-1, no m x m matrix anywhere
        step = -K @ z - (np.eye(23) - K @ H) @ np.linalg.solve(J, dx)
        x    = boxplus(x, step)
        if np.all(np.abs(step[0:3]) < tol[0]) and np.all(np.abs(step[3:6]) < tol[1]):
            break
    P_post = (np.eye(23) - K @ H) @ P
    return x, P_post
```

**Trick.** Never form `np.linalg.inv(HtRH + Pinv)`; solve. And recompute the 5-NN only on the *first* iteration or when the previous step was small (the code's `converge` flag) — the correspondences barely move after the first step and the search is the expensive part.

**In the original code.** `include/IKFoM_toolkit/esekfom/esekfom.hpp:1619` `update_iterated_dyn_share_modified`: $\mathbf{J}$ handling for the SO(3) blocks (`:1660-1679`) and $\mathbb{S}^2$ blocks (`:1680-1699`); the information-form gain for $n \le m$ — `P_temp = (P_/R).inverse(); P_temp.block<12,12>(0,0) += HTH;` then `K_h = P_inv * h_x^T * h` (`:1782-1809`); the state step `dx_ = K_h + (K_x - I) * dx_new` and `x_.boxplus(dx_)` (`:1815-1817`); the convergence test against `limit` (`:1819-1827`). The call site with `LASER_POINT_COV` is `src/laserMapping.cpp:960`; the toolkit is registered with `init_dyn_share` at `:828`.
https://github.com/hku-mars/FAST_LIO/blob/7cc4175de6f8ba2edf34bab02a42195b141027e9/include/IKFoM_toolkit/esekfom/esekfom.hpp#L1782-L1817

---

## C6 · ikd-Tree: the map that can be updated at scan rate

**What the paper specifies (§V).** A k-d tree whose nodes carry subtree point counts, deletion flags and bounding boxes, so that:
*insert* down-samples on the tree (keep the point nearest the voxel centre among those already in the voxel), *delete by box* marks whole subtrees lazily, and *re-balance* rebuilds a subtree when either criterion fires:
$$\alpha_{bal}:\ \max(n_{left}, n_{right}) < \alpha_{bal}\,(n_{left}+n_{right}),\qquad \alpha_{del}:\ n_{invalid} < \alpha_{del}\, n_{tree}$$
with large subtrees rebuilt in a second thread while the main thread keeps searching the old one.

**Code (ours, the honest version).** For the Python prototype use `scipy.spatial.cKDTree` rebuilt every $N$ scans over a voxel-hashed map — that is exactly the baseline the paper beats, and it is enough to validate C1–C5. Implement ikd-Tree only in the C++ port (see `implementation.md`, step 6).

```python
class VoxelMap:                                   # stand-in for the ikd-Tree in the prototype
    def __init__(self, voxel=0.5): self.voxel, self.pts, self.tree, self.dirty = voxel, {}, None, True
    def insert(self, P):
        for p in P:
            k = tuple(np.floor(p / self.voxel).astype(int))
            if k not in self.pts: self.pts[k] = p; self.dirty = True        # on-insert down-sampling, one point per voxel
    def query(self, p, k=5):
        if self.dirty: self.tree, self.dirty = cKDTree(np.array(list(self.pts.values()))), False
        return self.tree.data[self.tree.query(p, k)[1]]
```

**In the original code.** Public API `ikd-Tree/ikd_Tree.h:235-242` (`Build`, `Nearest_Search`, `Box_Search`, `Radius_Search`, `Add_Points(…, downsample_on)`, `Delete_Point_Boxes`); the two criteria `delete_criterion_param = 0.5f` and `balance_criterion_param = 0.7f` at `:194-195`, evaluated at `ikd-Tree/ikd_Tree.cpp:1100-1103`; `Rebuild` declared at `ikd_Tree.h:205`. How FAST-LIO2 uses it: the moving local map and box deletion in `src/laserMapping.cpp:231` `lasermap_fov_segment`, insertion with down-sampling in `:427` `map_incremental` (`ikdtree.Add_Points(PointToAdd, true)` at `:470`).
https://github.com/hku-mars/ikd-Tree/blob/c0e36a16b6e4d557d3783b16911207f6398dd478/ikd-Tree/ikd_Tree.h#L235-L242
