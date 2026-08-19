---
icon: simple/pandas
---

# Pandas

Notes written against **pandas 3.0**, which changed several long-standing
behaviours. Where 3.0 differs from the 1.x/2.x behaviour most tutorials still
describe, it is called out, because that gap is a common source of interview
answers that are now wrong.

### What Interviewers Actually Probe

Rarely the API surface, since that is lookup. Almost always one of these five:

| Probe | The question behind it |
| --- | --- |
| "Why is this slow?" | Do you understand vectorisation and dtypes? |
| "Why did my change not stick?" | Do you understand views, copies and Copy-on-Write? |
| "Why did the row count grow after a join?" | Do you understand merge cardinality? |
| "This works on 10k rows and dies on 50M." | Do you know when pandas is the wrong tool? |
| "How do you test this?" | Have you shipped a data pipeline, or only notebooks? |

### The Data Model

Three objects, and the `Index` is the one people underestimate.

- **`Index`** — an immutable labelled axis. It is not decoration: it drives
  alignment, joins and lookups.
- **`Series`** — a one-dimensional typed array plus an `Index`.
- **`DataFrame`** — a dict-like collection of `Series` sharing one row `Index`,
  with a second `Index` for the columns.

Alignment by index label, not by position, is the single most surprising
behaviour for people coming from SQL or NumPy:

```python
import pandas as pd

a = pd.Series([1, 2, 3], index=["x", "y", "z"])
b = pd.Series([10, 20, 30], index=["z", "y", "x"])

print((a + b).to_dict())
# {'x': 31, 'y': 22, 'z': 13}   <- z+x, y+y, x+z: aligned by LABEL, not position
```

If you wanted positional arithmetic you needed `a + b.to_numpy()`. Whole
categories of "the numbers are subtly wrong" bugs come from this, usually after
a `reset_index()` was forgotten or added.

### dtypes and Why They Matter

Everything about correctness and performance starts here.

| dtype | Backed by | Notes |
| --- | --- | --- |
| `int64`, `float64`, `bool` | NumPy | Fast, contiguous, no null support for ints |
| `Int64`, `Float64`, `boolean` | pandas nullable (masked) | Capitalised. Holds `pd.NA` without upcasting |
| `str` | pandas 3.0 default for text | **New default in 3.0.** Previously `object` |
| `object` | Python objects | The slow path: a pointer per element |
| `category` | integer codes + categories | Huge memory win on low-cardinality text |
| `datetime64[ns]`, `timedelta64[ns]` | NumPy | Use `tz` where the data is zoned |
| `ArrowDtype` | Apache Arrow | Opt-in via `dtype_backend="pyarrow"` |

!!! note "pandas 3.0 changed the default string dtype"
    Text columns now infer as `str`, not `object`. Old answers along the lines of
    "strings are always `object` dtype in pandas" are out of date. Checking
    `df.dtypes` before optimising anything is still the right first move.

The integer-plus-null trap, which is the classic dtype interview question:

```python
import pandas as pd

s = pd.Series([1, 2, 3])
print(s.dtype)                       # int64
print(s.reindex([0, 1, 2, 3]).dtype) # float64  <- a single missing value upcast the column

n = pd.Series([1, 2, None], dtype="Int64")   # nullable integer
print(n.tolist(), n.dtype, n.sum())          # [1, 2, <NA>] Int64 3
```

NumPy `int64` has no null representation, so introducing one missing value
converts the whole column to `float64`. Silently. Beyond 2^53 that loses
precision, which is how IDs get corrupted. Nullable `Int64` is the fix.

### Missing Data: `NaN`, `None`, `pd.NA`

Three sentinels with different semantics, and interviewers like this because it
separates people who have debugged real data from people who have not.

```python
import pandas as pd, numpy as np

print(np.nan == np.nan)      # False   -> IEEE 754: NaN is not equal to itself
print(repr(pd.NA == pd.NA))  # <NA>    -> propagates instead of returning a bool
print(pd.Series(["a", None]).isna().tolist())   # [False, True]
```

Practical rules:

- **Never compare to a null**, always `.isna()` / `.notna()`. `df[df.x == np.nan]`
  returns nothing, every time.
- `pd.NA` **propagates** through comparisons rather than collapsing to `False`,
  so a boolean mask built from nullable columns can itself contain `NA`. Use
  `.fillna(False)` on the mask before indexing.
- Aggregations skip nulls by default (`skipna=True`). `sum()` of an all-null
  column is `0`, not null, which surprises people reconciling totals.
- `dropna()` defaults to `how="any"` across **rows**. On wide frames that quietly
  deletes most of your data.

### Selection: `[]` vs `.loc` vs `.iloc`

| Accessor | Indexes by | Use for |
| --- | --- | --- |
| `df["col"]` | column label | Reading a single column |
| `df[boolean_mask]` | row mask | Filtering rows |
| `df.loc[rows, cols]` | **labels** (end-inclusive) | Almost everything, including writes |
| `df.iloc[rows, cols]` | **positions** (end-exclusive) | Positional work, `head`-like slicing |
| `df.at` / `df.iat` | single scalar | Hot loops needing one cell |

Two edges worth knowing: `.loc["a":"c"]` **includes** `"c"` while `.iloc[0:3]`
excludes position 3; and `df[0:2]` slices *rows* while `df["a"]` selects a
*column*, which is why `[]` is a poor habit for anything non-trivial.

**Write through a single `.loc` call**, never through two chained lookups:

```python
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

df.loc[df["a"] > 1, "b"] = 0     # correct: one indexing operation
print(df["b"].tolist())          # [4, 0, 0]
```

### Copy-on-Write and Chained Assignment

The behaviour that changed most in pandas 3.0, and the highest-value thing to
know here.

**Copy-on-Write (CoW) is always on in pandas 3.0 and cannot be disabled.** Any
DataFrame derived from another behaves as an independent copy, while pandas
still shares memory internally until a write forces a real copy. The consequence:
**modifying a derived object never affects its parent.**

```python
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3]})
sub = df[df["a"] > 1]
sub["a"] = 99

print(sub["a"].tolist())   # [99, 99]
print(df["a"].tolist())    # [1, 2, 3]  <- parent untouched, guaranteed
```

And chained assignment now fails loudly instead of maybe-working:

```python
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3]})
df["a"][0] = 99            # raises ChainedAssignmentError (a warning class)
print(df["a"].tolist())    # [1, 2, 3]  <- the write went to a temporary and was discarded
```

!!! warning "The 2.x answer is now wrong"
    Before 3.0 this raised `SettingWithCopyWarning` and *sometimes* mutated the
    original depending on the block layout, which is exactly why it was replaced.
    The modern answer is: CoW is mandatory, chained assignment raises
    `ChainedAssignmentError` and never writes through, and the fix is a single
    `.loc[mask, col] = value`.

This also makes `inplace=True` largely pointless. It never reliably saved memory,
and it breaks method chaining. Prefer reassignment:

```python
import pandas as pd

df = pd.DataFrame({"a": [3, 1, 2], "b": ["x", "y", "z"]})

out = (
    df.rename(columns={"b": "label"})
      .sort_values("a")
      .reset_index(drop=True)
)
print(out["a"].tolist())   # [1, 2, 3]
print(df["a"].tolist())    # [3, 1, 2]  <- unchanged; nothing is in place
```

### Vectorisation: Why `apply` and `iterrows` Are Slow

Ordered from fastest to slowest for the same work:

| Approach | Relative cost | Why |
| --- | --- | --- |
| Vectorised column arithmetic | 1x | One C loop over contiguous memory |
| `np.where` / `.mask` / `.clip` | ~1x | Same, for conditionals |
| `.map` on a `Series` with a dict | ~5x | Per-element, but no row assembly |
| `.apply(axis=0)` on a column | ~10x | Python call per element |
| `.apply(axis=1)` on rows | ~100x | Builds a `Series` per row |
| `for _, row in df.iterrows()` | ~500x | Builds a `Series` per row **and** coerces dtypes |

```python
import pandas as pd

df = pd.DataFrame({"price": [10.0, 20.0, 30.0], "qty": [1, 2, 3]})

df["total"] = df["price"] * df["qty"]                              # do this
# df["total"] = df.apply(lambda r: r["price"] * r["qty"], axis=1)  # not this
```

`iterrows` has a correctness problem on top of the speed one, because a row is a
`Series` and a `Series` has **one** dtype:

```python
import pandas as pd

df = pd.DataFrame({"i": [1, 2], "f": [1.5, 2.5]})

_, row = next(df.iterrows())
print(row.dtype, repr(row["i"]))     # float64 np.float64(1.0)  <- the int became a float

print(next(df.itertuples()))         # Pandas(Index=0, i=1, f=1.5)  <- types preserved
```

So if you genuinely must iterate, use `itertuples()`: it preserves dtypes and is
an order of magnitude faster than `iterrows()`.

`apply` is not banned. It is the right tool when the operation truly has no
vectorised form (calling an external API per row, parsing irregular text). Say
that in an interview rather than reciting "never use apply", and note that the
real fix for a slow `apply` is often a `merge` or a `map` against a lookup table.

### GroupBy: `agg` vs `transform` vs `filter` vs `apply`

Split, apply, combine. The distinction interviewers want is **what shape comes
back**.

```python
import pandas as pd

df = pd.DataFrame({"k": ["a", "a", "b", "b", "b"], "v": [1, 2, 3, 4, 5]})
g = df.groupby("k")

print(g["v"].sum().to_dict())              # {'a': 3, 'b': 12}       one row per group
print(g["v"].transform("sum").tolist())    # [3, 3, 12, 12, 12]      original shape
print(g.filter(lambda x: x["v"].sum() > 5)["v"].tolist())   # [3, 4, 5]  subset of rows
```

| Method | Returns | Use for |
| --- | --- | --- |
| `agg` | One row per group | Summaries |
| `transform` | Same shape as input | Group statistics broadcast back onto rows: shares of total, group-mean centring, per-group ranking |
| `filter` | Subset of original rows | Keeping whole groups that satisfy a predicate |
| `apply` | Anything | Last resort. Slow, and the return shape is inferred, so it is easy to get an unexpected index |

`transform` is the one that most often turns an ugly merge-back into one line:

```python
import pandas as pd

df = pd.DataFrame({"dept": ["a", "a", "b"], "salary": [100, 200, 300]})

df["dept_share"] = df["salary"] / df.groupby("dept")["salary"].transform("sum")
print(df["dept_share"].round(3).tolist())   # [0.333, 0.667, 1.0]
```

Named aggregation keeps output columns flat, which avoids the MultiIndex columns
that make downstream code miserable:

```python
import pandas as pd

df = pd.DataFrame({"k": ["a", "a", "b"], "v": [1, 2, 3]})

out = df.groupby("k").agg(total=("v", "sum"), n=("v", "size"), avg=("v", "mean"))
print(out.to_dict())   # {'total': {'a': 3, 'b': 3}, 'n': {'a': 2, 'b': 1}, 'avg': {'a': 1.5, 'b': 3.0}}
```

!!! note "`observed=True` is the pandas 3.0 default"
    Grouping by a `category` used to return a row for **every** declared
    category, including ones absent from the data, which produced huge sparse
    results. In 3.0 unobserved combinations are dropped by default. Pass
    `observed=False` if you actually want the zero rows:

    ```python
    import pandas as pd

    df = pd.DataFrame({"k": pd.Categorical(["a", "a"], categories=["a", "b"]), "v": [1, 2]})

    print(df.groupby("k")["v"].sum().to_dict())                  # {'a': 3}
    print(df.groupby("k", observed=False)["v"].sum().to_dict())   # {'a': 3, 'b': 0}
    ```

Also remember `dropna=True` is the groupby default, so **rows with a null key
disappear from the output entirely**. On a revenue report that is a silent
under-count.

### Merging and Joining Safely

`merge` is SQL join semantics; `join` is a convenience wrapper that defaults to
joining on the index; `concat` is stacking.

The senior answer to "the row count grew after the join" is that you asserted
nothing about cardinality. Two arguments prevent an entire class of production
incidents:

```python
import pandas as pd

left = pd.DataFrame({"id": [1, 2], "x": ["a", "b"]})
right = pd.DataFrame({"id": [2, 2, 3], "y": ["p", "q", "r"]})

m = left.merge(right, on="id", how="outer", indicator=True)
print(m["_merge"].tolist())
# ['left_only', 'both', 'both', 'right_only']   <- exactly what matched, and what did not

try:
    left.merge(right, on="id", validate="one_to_one")
except pd.errors.MergeError as e:
    print(type(e).__name__, str(e).splitlines()[0])
    # MergeError Merge keys are not unique in right dataset; not a one-to-one merge
```

- **`validate=`** takes `"one_to_one"`, `"one_to_many"`, `"many_to_one"` or
  `"many_to_many"` and raises rather than silently fanning out rows. Use it on
  every join in a pipeline where you believe you know the cardinality.
- **`indicator=True`** adds a `_merge` column, which turns "why are there
  nulls?" into a two-line check.
- **`suffixes=`** should be set explicitly. The `_x` / `_y` defaults are how you
  end up with `revenue_x` in a dashboard.
- **Key dtypes must match.** An `int64` key will not join to a `str` key of the
  same digits, and you get zero matches with no error. Check dtypes first.
- `how="left"` plus a duplicated right key **multiplies** rows. Deduplicate the
  right side, or aggregate it, before joining.

### Reshaping

| Operation | Direction | Notes |
| --- | --- | --- |
| `pivot` | long to wide | Raises if the index/column pair is duplicated |
| `pivot_table` | long to wide | Aggregates duplicates (`aggfunc`), so it never raises on them |
| `melt` | wide to long | The inverse of `pivot` |
| `stack` / `unstack` | move a level between index and columns | Works on MultiIndex |
| `explode` | one list-valued cell to many rows | Cleaning nested payloads |

```python
import pandas as pd

sales = pd.DataFrame({"region": ["e", "e", "w", "w"],
                      "quarter": ["q1", "q2", "q1", "q2"],
                      "amount": [1, 2, 3, 4]})

wide = sales.pivot_table(index="region", columns="quarter", values="amount", aggfunc="sum")
print(wide.to_dict())        # {'q1': {'e': 1, 'w': 3}, 'q2': {'e': 2, 'w': 4}}

long = wide.reset_index().melt(id_vars="region", var_name="quarter", value_name="amount")
print(len(long))             # 4
```

Rule of thumb: `pivot` when duplicates are a bug you want to hear about,
`pivot_table` when they are expected and should be aggregated.

### Time Series

`resample` is groupby for a `DatetimeIndex`, and it is what the question "roll
this up to weekly" is really asking for.

```python
import pandas as pd

ts = pd.Series(range(10), index=pd.date_range("2026-01-01", periods=10, freq="D"))

print(ts.resample("W").sum().to_dict())
# {Timestamp('2026-01-04'): 6, Timestamp('2026-01-11'): 39}   <- W anchors to Sunday
```

Points worth making:

- **`resample` changes the frequency** (aggregating or filling); `asfreq` only
  re-labels onto a new frequency; `rolling` keeps the frequency and computes over
  a moving window; `shift` moves values in time, which is how you build lags
  without leaking future data into a model.
- **The anchor matters.** `"W"` means week-ending-Sunday. Use `"W-MON"` or
  `label="left"` / `closed="left"` when the business definition differs. Silent
  off-by-one-week reporting bugs live here.
- **Store UTC, convert at the edges.** `tz_localize` attaches a zone to naive
  timestamps; `tz_convert` moves an aware timestamp between zones. Mixing naive
  and aware timestamps raises, which is the good outcome.
- Sort the index before slicing by time, and prefer a real `DatetimeIndex` over
  string dates, which sort lexicographically and compare wrongly.

### Performance and Memory

Roughly in order of payoff:

1. **Fix dtypes.** `category` for low-cardinality text is often a 50x memory win:

    ```python
    import pandas as pd

    s = pd.Series(["alpha", "beta", "gamma"] * 100_000)
    print(s.memory_usage(deep=True))                    # 16100132   (~16 MB)
    print(s.astype("category").memory_usage(deep=True)) # 300293     (~0.3 MB)
    ```

1. **Read less.** `pd.read_csv(..., usecols=[...], dtype={...}, parse_dates=[...])`
   avoids materialising columns you will drop and avoids a second inference pass.
   Prefer Parquet over CSV: typed, columnar, compressed, and it supports column
   pruning at read time.
1. **Vectorise**, per the table above.
1. **Avoid repeated concatenation in a loop.** Each `pd.concat` copies. Build a
   list and concatenate once.
1. **Stream in chunks** with `chunksize=` when the file exceeds memory, and
   aggregate per chunk.
1. **`query` / `eval`** for large multi-condition filters: fewer intermediate
   boolean arrays.
1. **Profile before guessing.** `df.info(memory_usage="deep")` and
   `df.memory_usage(deep=True)` tell you where the bytes are; `%timeit` tells you
   whether your change helped.

Rough working number: pandas wants roughly **5 to 10x the raw data size** in RAM
for comfortable work, because intermediates are copies.

### Testing DataFrames

The thing that distinguishes a pipeline engineer from a notebook user.

```python
import pandas as pd

got = pd.DataFrame({"a": [1]})
want = pd.DataFrame({"a": [1.0]})

try:
    pd.testing.assert_frame_equal(got, want)
except AssertionError as e:
    print(str(e).splitlines()[0])
    # Attributes of DataFrame.iloc[:, 0] (column name="a") are different

pd.testing.assert_frame_equal(got, want, check_dtype=False)   # passes
```

- `assert_frame_equal` / `assert_series_equal` compare values **and** dtype,
  index and column order. Relax deliberately with `check_dtype=False`,
  `check_like=True` (ignore column/row order) or `rtol=` / `atol=` for floats.
- **Never assert on floats with `==`.** Use tolerances.
- **Test the transformation, not the I/O.** Build small literal DataFrames as
  fixtures; keep file reading in a thin layer you can stub.
- **Assert invariants in production code too**, not only in tests: expected row
  counts, no unexpected nulls in key columns, keys unique after a join. A
  pipeline that fails fast beats a dashboard that is quietly wrong.

### When to Leave pandas

An answer worth having ready, because it shows you know the tool's edges.

| Situation | Better tool |
| --- | --- |
| Fits in RAM but single-threaded pandas is slow | **Polars** or **DuckDB** (multi-core, lazy, query-optimised) |
| Data lives in a warehouse | **SQL**. Push the aggregation down; do not pull 50M rows to filter them locally |
| Bigger than one machine's RAM, batch | **[PySpark](pyspark.md)** or **Dask** |
| Streaming or continuous | **Spark Structured Streaming**, **Flink** |
| Interactive analysis on files just past RAM | **DuckDB** over Parquet, often the cheapest fix |

pandas remains the right default for exploratory work, feature engineering on
moderate data, and as the last-mile shaper before a chart or a model. The failure
mode to name is using it as an ETL engine on data that never fitted comfortably
in memory.

### Common Gotchas

| Symptom | Cause |
| --- | --- |
| Assignment "did nothing" | Chained assignment. In 3.0 it raises `ChainedAssignmentError`; use one `.loc[mask, col] = ...` |
| Column became `float` | A null was introduced into an `int64` column. Use `Int64` |
| Filter returns no rows | Comparing against a null with `==`, or mismatched key dtypes |
| Row count grew after a join | Duplicated join keys. Add `validate=` |
| Rows vanished after `groupby` | `dropna=True` default dropped null keys |
| Category rows missing from a groupby | `observed=True` is the 3.0 default; pass `observed=False` |
| Numbers subtly wrong after arithmetic | Index alignment. Check with `.index.equals(...)` |
| `MultiIndex` columns everywhere | `agg` with a list. Use named aggregation |
| Weekly totals off by one week | `resample("W")` anchors to Sunday; set the anchor or `closed`/`label` |
| Memory blew up on read | No `dtype=` / `usecols=`; text stored uncategorised |
| Slow row-wise work | `apply(axis=1)` or `iterrows`; vectorise, or `itertuples` |

### Interview Summary

> The mental model I lead with is that a DataFrame is typed columns plus an
> index, and almost every surprise comes from one of those two. The index causes
> it when arithmetic or a join aligns on labels rather than positions. The dtypes
> cause it when a single null upcasts an `int64` column to `float64` and quietly
> costs precision on IDs, which is why I reach for nullable `Int64` and `category`
> early. On pandas 3.0 specifically, Copy-on-Write is mandatory, so a derived
> frame never writes through to its parent and chained assignment raises
> `ChainedAssignmentError` instead of sometimes working. That makes the old
> `SettingWithCopyWarning` advice obsolete and makes `inplace=True` pointless, so
> I write one `.loc[mask, col] = value` and chain methods. For performance I fix
> dtypes first, then vectorise, and I treat `apply(axis=1)` and `iterrows` as
> smells rather than crimes. And I put assertions in the pipeline, not just the
> tests: `validate=` on every merge, expected row counts, uniqueness after joins.
> When the data stops fitting comfortably I would rather push the work into SQL,
> DuckDB or Spark than keep tuning pandas.

### References

- [pandas user guide.](https://pandas.pydata.org/docs/user_guide/index.html)

- [Copy-on-Write.](https://pandas.pydata.org/docs/user_guide/copy_on_write.html)

- [Scaling to large datasets.](https://pandas.pydata.org/docs/user_guide/scale.html)

- [Nullable integer data type.](https://pandas.pydata.org/docs/user_guide/integer_na.html)

- [pandas 3.0 release notes.](https://pandas.pydata.org/docs/whatsnew/v3.0.0.html)
