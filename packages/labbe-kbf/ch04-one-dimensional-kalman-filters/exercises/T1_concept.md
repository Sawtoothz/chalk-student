# T1 — Concept check

Answer in one or two sentences each. Then compare with `solutions/T1.md`. Names: R_proc = Labbe's Q (process
variance), Q_meas = Labbe's R (sensor variance).

1. The chapter replaces the discrete-Bayes histogram with two numbers. Which two, and what must be true of the
   predict and update operations for that replacement to survive a whole run (p. 134)?
2. Predict always increases the variance; update always leaves a variance smaller than both the prior's and the
   measurement's. Give the one-line reason for each.
3. The book's "Modify Variance Values" exercise (p. 148), before computing anything: with (R_proc, Q_meas) = (40, 2)
   and then (2, 40), which run has the smaller steady posterior variance, and which one has the smoother plot? Are those
   the same run?
4. P never looks at a measurement (pp. 138, 146). Name one thing an embedded engineer gains from that, and one thing it
   means P cannot tell you.
5. You paste `kf.update(x, P, z, R)` from FilterPy (p. 168) into code that follows Thrun's names. What goes wrong, and
   what would you see in the plot?
6. What do K → 0 and K → 1 mean, in terms of which variance dominates, and what does the filter do in each limit?
   Which chapter-1 filter is this, and what does the Kalman filter add to it (pp. 150–153)?
7. The thermometer (pp. 155–158) measures a constant voltage, yet the book keeps a nonzero process variance. Why, and
   what does a too-small one do (the "smug" filter)?
8. In the incorrect-process-variance example (pp. 160–161) the filter diverges while its P looks perfectly confident.
   Which quantity, computed inside the filter at every step, exposes the problem? Why can P not?
9. The Nonlinear Systems exercise (pp. 165–167) tracks a sine with a process model N(1, 2) and attributes the offset to
   nonlinearity. Is a sine in time a nonlinear system? Where does the offset really come from?
10. When would you ship the fixed-gain filter of p. 168 instead of the full filter on a robot, and what three things do
    you give up?
