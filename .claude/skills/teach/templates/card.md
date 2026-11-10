## C<n>. <Algorithm or equation family>, <book table / eq.>

**Shapes.** <every symbol with dimensions>

**Naive (reads like the book).**

```python
def <name>(...):
    ...   # line 2
```

**Robust.**

```python
def <name>(...):
    ...
```

Tricks, each one named:

1. **<trick>.** <why, one or two sentences>.
2. ...

**Eigen.**

```cpp
template <int N, int K>
...
```

**Cost per step.** <big-O and which product dominates in practice>

**What breaks first.** <ordered: first failure mode, then the next>

**In the original code.** <only for papers, and only from `code_refs.json`: `path:line` of the function that
implements this equation, what to look at there, the authors' own comments worth reading, then one permalink at the
pinned commit. If the authors published no code: "No reference implementation from the authors; closest anchored
implementation: <repo @ commit, path:line>.">
