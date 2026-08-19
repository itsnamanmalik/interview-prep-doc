---
icon: simple/apachespark
---

# PySpark

Notes written against **Spark 3.5**, verified on a local Spark session. PySpark is
the Python API over Spark SQL; almost every interview question about it is really
a question about **partitions, shuffles and serialisation boundaries**.

### What Interviewers Actually Probe

| Probe | The question behind it |
| --- | --- |
| "This job takes 4 hours. Where would you look?" | Do you think in stages and shuffles, or in lines of code? |
| "Why is one task still running when 199 finished?" | Do you understand data skew? |
| "Why is your UDF slow?" | Do you understand the JVM/Python boundary? |
| "How big does data need to be before you reach for Spark?" | Do you know its overhead, or is it a reflex? |
| "How do you know the job is correct?" | Have you tested a distributed pipeline? |

### When Spark Is the Right Tool

Spark's cost is real: JVM startup, cluster provisioning, serialisation, shuffle
I/O, and a much harder debugging story than a single process. Reach for it when
**one machine genuinely cannot do the job**.

| Situation | Reach for |
| --- | --- |
| Under a few GB | [pandas](pandas.md), Polars, DuckDB |
| Tens of GB on one big machine | Polars or DuckDB, usually faster than Spark and far simpler |
| Hundreds of GB to petabytes, batch | **Spark** |
| Data already in a warehouse | SQL in the warehouse; do not export it to Spark to filter it |
| Continuous / event streams | Spark Structured Streaming, or Flink |
| Heterogeneous files, schema drift, huge shuffles | **Spark** |

The honest senior answer is that "Spark because the data is big" is a
justification you should be able to quantify. Below roughly 100 GB, a single
modern machine with DuckDB or Polars usually wins on both wall clock and
engineering time.

### Architecture

```
Driver  (your Python process + the SparkContext / SparkSession)
  │   builds the logical plan, schedules stages, tracks metadata
  │
Cluster manager  (YARN, Kubernetes, Standalone)
  │   allocates executors
  │
Executors  (JVM processes, N cores each)
      run tasks, hold cached partitions, and each fork Python workers for UDFs
```

| Term | Definition |
| --- | --- |
| **Partition** | The unit of parallelism. One partition is processed by one task |
| **Task** | Work on one partition by one core |
| **Stage** | A set of tasks with no shuffle between them. A shuffle boundary ends a stage |
| **Job** | Everything triggered by one action |
| **Executor** | A JVM with a fixed core and memory allocation |

The rule that follows: **your maximum parallelism is `min(partitions, total
executor cores)`.** A 2,000-core cluster running a job with 8 partitions is a
2,000-core cluster running on 8 cores.

!!! warning "The driver is not a worker"
    `collect()`, `toPandas()` and `count()` on a wide frame pull data to the
    driver. `collect()` on a large DataFrame is the most common way to OOM a
    Spark job, and the traceback points at the driver, not the data. Use
    `limit()` and `show()` while exploring, and write results out rather than
    collecting them.

### Lazy Evaluation

Transformations build a plan; nothing executes until an action asks for a result.

| Transformations (lazy) | Actions (trigger a job) |
| --- | --- |
| `select`, `filter`, `withColumn`, `join`, `groupBy().agg()`, `orderBy`, `repartition`, `union` | `show`, `count`, `collect`, `take`, `first`, `write`, `toPandas`, `foreach` |

```python
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("demo").master("local[4]").getOrCreate()

df = spark.range(0, 1000).withColumn("grp", (F.col("id") % 5).cast("int"))
filtered = df.filter(F.col("id") > 100).select("grp")   # nothing has run yet
print(filtered.count())                                  # 899 -- this ran it
```

Two consequences worth naming:

- **Laziness is what allows optimisation.** Catalyst sees the whole plan, so it
  can push filters down to the scan, prune columns, and reorder joins.
- **Every action re-runs the lineage.** Calling `count()` then `show()` on the
  same expensive chain computes it twice. That is what `cache()` is for.

### The Shuffle

The single most important concept. A **shuffle** redistributes data across
executors over the network, writing intermediate files to disk on the way.

| Narrow transformation | Wide transformation (shuffles) |
| --- | --- |
| Each output partition depends on one input partition | Each output partition depends on many input partitions |
| `select`, `filter`, `withColumn`, `map`, `union`, `coalesce` | `groupBy`, `join` (non-broadcast), `distinct`, `orderBy`, `repartition`, window functions |

Why it dominates cost: disk write, network transfer, disk read, plus a stage
barrier where every task waits for the slowest one.

How to spend less on it:

1. **Filter and project before the shuffle**, not after. Shuffle fewer bytes.
1. **Broadcast the small side of a join** so there is no shuffle at all.
1. **Pre-aggregate** where possible: `reduceByKey`-style partial aggregation beats
   moving raw rows. The DataFrame API does this for you, which is one reason to
   prefer it over RDDs.
1. **Size `spark.sql.shuffle.partitions` deliberately.** The default is **200**,
   which is wrong for both small and huge jobs. Aim for partitions in the
   **128 MB to 256 MB** range.
1. **Avoid `orderBy` unless you need global ordering.** It shuffles everything.
   `sortWithinPartitions` is often what was actually wanted.

### RDDs, DataFrames and Catalyst

| API | Optimised by Catalyst | Use when |
| --- | --- | --- |
| **DataFrame / Spark SQL** | Yes | Default for everything |
| **RDD** | No | Truly unstructured data, or custom partitioning logic you cannot express in SQL |
| **Dataset** | Yes | JVM only. **There is no typed `Dataset` in PySpark**, which is a real interview question |

Two names to be able to explain:

- **Catalyst** — the query optimiser. It rewrites your plan: predicate pushdown,
  column pruning, constant folding, join reordering.
- **Tungsten** — the execution engine. Off-heap binary memory layout, cache-aware
  processing, and whole-stage code generation that compiles a chain of operators
  into a single generated Java method to avoid virtual calls per row.

The practical implication: **expressing work in DataFrame operations and
built-in functions lets Catalyst and Tungsten optimise it. A Python UDF is a
black box that defeats both.**

### Adaptive Query Execution

AQE is **enabled by default from Spark 3.2**, and it changes several classic
interview answers.

At each shuffle boundary AQE looks at real runtime statistics and re-plans:

| AQE feature | What it does |
| --- | --- |
| **Coalesce shuffle partitions** | Merges small post-shuffle partitions, so the 200 default no longer produces 200 tiny files |
| **Switch join strategy** | Converts a planned sort-merge join to a broadcast join once it sees the real side size |
| **Skew join handling** | Splits oversized partitions into subtasks |

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("aqe").master("local[4]").getOrCreate()

print(spark.conf.get("spark.sql.adaptive.enabled"))                      # true
print(spark.conf.get("spark.sql.adaptive.coalescePartitions.enabled"))   # true
print(spark.conf.get("spark.sql.adaptive.skewJoin.enabled"))             # true
```

So "always tune `spark.sql.shuffle.partitions` by hand" is a pre-3.x answer. The
current answer is: set a sensible upper bound and let AQE coalesce, then tune by
hand only when you can show AQE got it wrong.

### Joins

| Strategy | Mechanism | Chosen when |
| --- | --- | --- |
| **Broadcast hash join** | Small side shipped to every executor, no shuffle | One side under `spark.sql.autoBroadcastJoinThreshold`, default **10 MB** |
| **Sort-merge join** | Both sides shuffled by key and sorted | The default for two large sides |
| **Shuffle hash join** | Both shuffled, hash table built on one side | Chosen occasionally, or forced with a hint |
| **Broadcast nested loop** | Cartesian-ish fallback | Non-equi joins. Watch for this in a plan; it is usually a bug |

```python
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("joins").master("local[4]").getOrCreate()

facts = spark.range(0, 10_000).withColumn("grp", (F.col("id") % 5).cast("int"))
dims = spark.createDataFrame([(i, f"name{i}") for i in range(5)], ["grp", "name"])

joined = facts.join(F.broadcast(dims), "grp")     # force it, do not hope for it
joined.explain(mode="simple")                     # look for BroadcastHashJoin
```

- **Raise the threshold or use `F.broadcast()` explicitly** for dimension tables.
  Relying on the 10 MB default means a slightly-grown lookup table silently
  becomes a full shuffle join.
- **Never broadcast something that is not small.** It is materialised in every
  executor's memory and on the driver first.
- **Join key dtypes must match**, exactly as in pandas. A `string` key against a
  `bigint` key yields zero rows, quietly.
- **Nulls do not join.** Rows with a null key are dropped from an inner join. Use
  `eqNullSafe` if null-equals-null is the intent.
- **Duplicated keys multiply rows.** Deduplicate or aggregate before joining;
  Spark will not warn you.

### Data Skew

The classic "199 of 200 tasks finished in seconds, one has been running for an
hour" symptom. One key holds a disproportionate share of the rows, so one
partition holds most of the data, and the stage cannot finish until that task
does.

Diagnose it by counting rows per key, and by looking at the max-versus-median
task duration in the Spark UI.

```python
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("skew").master("local[4]").getOrCreate()

df = spark.range(0, 1000).withColumn(
    "k", F.when(F.col("id") < 990, F.lit("hot")).otherwise(F.lit("cold")))

print(df.groupBy("k").count().orderBy(F.desc("count")).collect())
# [Row(k='hot', count=990), Row(k='cold', count=10)]   <- 99% on one key
```

Fixes, in the order worth trying:

1. **Let AQE handle it.** `spark.sql.adaptive.skewJoin.enabled` splits skewed
   partitions automatically, and handles the common cases well.
1. **Broadcast the other side**, if it is small. No shuffle means no skew.
1. **Salt the key**: append a random bucket to the hot key so it spreads across
   partitions, and explode the small side to match.

    ```python
    from pyspark.sql import SparkSession, functions as F

    spark = SparkSession.builder.appName("salt").master("local[4]").getOrCreate()

    SALTS = 8
    facts = spark.range(0, 1000).withColumn("k", F.lit("hot"))
    dims = spark.createDataFrame([("hot", "value")], ["k", "v"])

    # spread the hot key over SALTS partitions
    f = facts.withColumn("salt", (F.rand(seed=42) * SALTS).cast("int"))
    # replicate the small side once per salt so the join still matches
    d = (dims.withColumn("salt", F.explode(F.array([F.lit(i) for i in range(SALTS)]))))

    out = f.join(d, on=["k", "salt"])
    print(out.count())      # 1000 -- same result, spread over 8 partitions
    ```

1. **Handle the hot key separately**: filter it out, aggregate it on its own,
   union the results back.
1. **Filter nulls early.** A null key is very often the actual hot key.

### Partitioning

Two different things share the word, and conflating them is a common interview
stumble.

**In-memory partitioning** controls parallelism:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("parts").master("local[4]").getOrCreate()

df = spark.range(0, 1000)
print(df.rdd.getNumPartitions())                         # 4
print(df.repartition(8).rdd.getNumPartitions())          # 8   full shuffle
print(df.repartition(8).coalesce(2).rdd.getNumPartitions())  # 2   no shuffle
print(df.coalesce(16).rdd.getNumPartitions())            # 4   coalesce cannot increase
```

| | `repartition(n)` | `coalesce(n)` |
| --- | --- | --- |
| Shuffles | Yes, full | No, merges local partitions |
| Can increase count | Yes | **No** |
| Result balance | Even | Possibly uneven |
| Use for | Fixing skew, increasing parallelism, partitioning by key | Reducing file count before a write |

The subtle trap: `coalesce(1)` before a write does not just merge files, it
**reduces the parallelism of the upstream stage too**, because there is no
shuffle boundary to isolate it. If you need one output file from a wide
computation, use `repartition(1)` so the expensive work still runs in parallel.

**On-disk partitioning** controls what can be skipped at read time:

```python
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("write").master("local[4]").getOrCreate()

events = spark.range(0, 1000).withColumn("day", (F.col("id") % 3).cast("int"))
events.write.mode("overwrite").partitionBy("day").parquet("/tmp/events_demo")

back = spark.read.parquet("/tmp/events_demo")
back.filter(F.col("day") == 1).explain(mode="simple")   # PartitionFilters in the plan
```

- **Partition by low-cardinality columns you filter on**, typically a date.
  Partitioning by `user_id` creates millions of directories and destroys the job.
- **Aim for files of roughly 128 MB to 1 GB.** The **small-files problem** is the
  most common self-inflicted Spark wound: a partitioned write from 200 in-memory
  partitions creates 200 files *per* directory, and the next job spends its life
  listing and opening them.
- **`PartitionFilters` in the plan means directories were skipped;
  `PushedFilters` means the Parquet reader skipped row groups.** Checking for
  both is how you prove pruning is working rather than assuming it.

### Caching and Persistence

```python
from pyspark import StorageLevel          # note: pyspark, not pyspark.sql
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("cache").master("local[4]").getOrCreate()

df = spark.range(0, 1000).filter("id > 10")
df.cache()          # lazy: nothing is stored yet
df.count()          # this materialises it
print(df.storageLevel)                   # Disk Memory Deserialized 1x Replicated
print(StorageLevel.MEMORY_AND_DISK)      # Disk Memory Serialized 1x Replicated
df.unpersist()
print(df.storageLevel)                   # Serialized 1x Replicated  (nothing cached)
```

Note the difference in those two lines: `DataFrame.cache()` uses
**`MEMORY_AND_DISK_DESER`**, keeping rows deserialised in memory, whereas the
RDD-era `StorageLevel.MEMORY_AND_DISK` constant is the serialised variant. So
"`cache()` is just `persist(MEMORY_AND_DISK)`" is not quite right for DataFrames.

| Point | Detail |
| --- | --- |
| `cache()` is lazy | Nothing is stored until an action runs |
| Default level | `MEMORY_AND_DISK_DESER` for DataFrames |
| Useful levels | `MEMORY_ONLY`, `MEMORY_AND_DISK`, `DISK_ONLY`, `*_SER` variants |
| Always `unpersist()` | Cached data competes with execution memory for the whole job otherwise |

**Cache only when a DataFrame is reused, and reused more than the cost of storing
it.** Caching a frame used once makes the job slower. Caching too much causes
eviction thrashing and spills. In an interview, "I would cache it" is only a good
answer if you can say how many times it is read and why recomputation is more
expensive than the memory pressure.

### UDFs and the Python Boundary

This is where PySpark differs most from Scala Spark, and it is a favourite
question.

A **Python UDF** forces every row out of the JVM, through serialisation, into a
Python worker process, and back. Catalyst cannot see inside it, so no pushdown,
no code generation.

| Approach | Cost | Notes |
| --- | --- | --- |
| **Built-in functions** (`pyspark.sql.functions`) | Baseline | Runs in the JVM, fully optimised. Always try this first |
| **`pandas_udf`** (vectorised, Arrow) | Low | Batches of rows as a `pandas.Series` via Arrow. Usually several times faster than a row-at-a-time UDF |
| **Python `udf`** | High | Row-at-a-time, per-row serialisation, opaque to Catalyst |
| **RDD `map` with Python** | Highest | No Catalyst at all |

```python
import pandas as pd
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.functions import pandas_udf

spark = SparkSession.builder.appName("udf").master("local[4]").getOrCreate()

df = spark.range(0, 100).withColumn("v", (F.col("id") % 7).cast("int"))

# 1. Built-in: best.
df.select((F.col("v") + 1).alias("plus1")).limit(2).collect()

# 2. Vectorised pandas UDF: when there is no built-in equivalent.
@pandas_udf("int")
def plus1_vec(s: pd.Series) -> pd.Series:
    return s + 1

df.select(plus1_vec("v").alias("plus1")).limit(2).collect()

# 3. Row-at-a-time Python UDF: last resort.
plus1 = F.udf(lambda x: x + 1, "int")
df.select(plus1("v").alias("plus1")).limit(2).collect()
```

Additional UDF facts worth having ready:

- **Always declare the return type.** An unspecified type means `StringType`.
- **A Python UDF is not null-safe.** It receives `None` and will raise unless you
  handle it; the failure surfaces as an executor exception mid-job.
- **`pandas_udf` needs PyArrow**, and `spark.sql.execution.arrow.pyspark.enabled`
  also accelerates `toPandas()` and `createDataFrame()` from pandas.
- **Python workers use memory outside the executor JVM heap.** That is what
  `spark.executor.pyspark.memory` and container overhead are for, and forgetting
  it is a common cause of YARN or Kubernetes killing containers.

!!! warning "Spark 3.5 `pandas_udf` needs Python 3.11 or older"
    PySpark 3.5's pandas-UDF version check imports `distutils`, which was removed
    from the standard library in Python 3.12, so defining a `pandas_udf` on
    Python 3.12+ fails with `ModuleNotFoundError: No module named 'distutils'`
    before your function ever runs. Pin the interpreter to 3.11 or move to
    Spark 4.x. Worth knowing because the error names `distutils` and looks like a
    packaging problem rather than a version-compatibility one.

### Window Functions

```python
from pyspark.sql import SparkSession, Window, functions as F

spark = SparkSession.builder.appName("win").master("local[4]").getOrCreate()

df = spark.range(0, 20).withColumn("grp", (F.col("id") % 4).cast("int"))

w = Window.partitionBy("grp").orderBy(F.col("id").desc())
latest = df.withColumn("rn", F.row_number().over(w)).filter("rn = 1")

print(sorted(r["grp"] for r in latest.collect()))   # [0, 1, 2, 3] -- one row per group
```

- `partitionBy` in a `Window` is a **shuffle**, unrelated to file partitioning.
- A window **without** `partitionBy` moves the entire dataset into one partition.
  Spark warns about it, and it is a guaranteed OOM at scale.
- `row_number` / `rank` / `dense_rank` differ on ties: no ties, gaps on ties, no
  gaps on ties. Interviewers ask this exact question.
- The deduplication idiom is `row_number` over a window plus `filter("rn = 1")`,
  which also gives you "latest record per key" for free.

### Reading Data and Schemas

```python
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

spark = SparkSession.builder.appName("read").master("local[4]").getOrCreate()

schema = StructType([
    StructField("id", IntegerType(), nullable=False),
    StructField("name", StringType(), nullable=True),
])
print(spark.createDataFrame([(1, "a")], schema).schema.simpleString())
# struct<id:int,name:string>
```

- **Always supply a schema for CSV and JSON.** `inferSchema=True` reads the whole
  file an extra time and still gets types wrong at the edges. Parquet carries its
  own schema, so this does not apply there.
- **`mode`**: `PERMISSIVE` (default, nulls the bad row and can fill
  `_corrupt_record`), `DROPMALFORMED`, `FAILFAST`. Pick deliberately. Silent
  `PERMISSIVE` behaviour is how a pipeline "succeeds" with nulls everywhere.
- **Parquet or ORC over CSV/JSON.** Columnar, typed, compressed, and they support
  column pruning and predicate pushdown, which text formats cannot.
- **Table formats (Delta, Iceberg, Hudi)** add ACID commits, schema evolution and
  time travel over Parquet, and they solve the small-files problem with
  compaction. Worth naming as the modern default for a lakehouse.

### Structured Streaming

The same DataFrame API over an unbounded table, executed as micro-batches.

| Concept | Meaning |
| --- | --- |
| **Trigger** | How often a micro-batch runs; `availableNow` for batch-like catch-up |
| **Watermark** | How long to wait for late events before finalising a window and dropping state |
| **Output modes** | `append` (new rows only), `update` (changed aggregates), `complete` (whole result) |
| **Checkpoint** | Offsets plus state on durable storage. This is what makes restarts exactly-once |
| **State store** | Where aggregation and join state lives between batches |

```python
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("stream").master("local[2]").getOrCreate()

# rate is a built-in test source: one row per second with a timestamp.
stream = spark.readStream.format("rate").option("rowsPerSecond", 5).load()

agg = (stream
       .withWatermark("timestamp", "10 minutes")
       .groupBy(F.window("timestamp", "1 minute"))
       .count())

# .writeStream.format("console").outputMode("update") \
#     .option("checkpointLocation", "/tmp/ckpt").start()
```

Three points that separate real experience from reading:

- **Exactly-once is end-to-end only if the sink is idempotent or transactional.**
  Spark guarantees its own offsets and state; a sink that double-writes on
  retry breaks the guarantee regardless.
- **Watermarks trade completeness for bounded state.** Too short drops late data;
  too long grows the state store until it OOMs.
- **Never delete a checkpoint to "reset" a production stream** unless you intend
  to reprocess or lose position. Changing the query plan can also make an old
  checkpoint incompatible.

### Debugging and Tuning

**Read the plan first.**

```python
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("plan").master("local[4]").getOrCreate()

df = spark.range(0, 1000).withColumn("grp", (F.col("id") % 5).cast("int"))
df.filter(F.col("id") > 100).groupBy("grp").count().explain(mode="formatted")
```

What to look for, in order:

| In the plan / UI | Meaning |
| --- | --- |
| `Exchange` | A shuffle. Count them; each one is a stage boundary |
| `BroadcastHashJoin` vs `SortMergeJoin` | Whether the small side was actually broadcast |
| `PartitionFilters` / `PushedFilters` | Whether pruning and pushdown happened |
| `BroadcastNestedLoopJoin` | Usually an accidental non-equi join |
| Max task time versus median in a stage | Skew |
| Spill (memory and disk) metrics | Partitions too large; increase partition count |
| GC time high | Executor memory pressure, often from caching too much |

Common causes of failure, and what they actually mean:

- **Driver OOM** — `collect()` / `toPandas()` on something large, or a broadcast
  that was not small.
- **Executor OOM** — partitions too big, a window without `partitionBy`, or heavy
  skew. Increase partitions before increasing memory.
- **Container killed by YARN/Kubernetes** — off-heap and Python worker memory
  exceeded the overhead allowance, not the JVM heap.
- **Job hangs at 99%** — skew, nearly always.
- **Slow with no obvious hotspot** — small-files problem on the input.

### PySpark vs pandas

| | pandas | PySpark |
| --- | --- | --- |
| Execution | Eager, single process | Lazy, distributed |
| Scale ceiling | One machine's RAM | Cluster |
| Index | First-class | **No index concept** |
| Ordering | Preserved | Not guaranteed without `orderBy` |
| Mutation | In-place possible | Immutable, always a new DataFrame |
| Types | NumPy/pandas dtypes | Spark SQL types, explicit schema |
| Overhead on small data | None | Seconds to minutes |
| Debugging | Print anything | Read plans and the UI |

**Pandas API on Spark** (`pyspark.pandas`, formerly Koalas) offers a pandas-like
surface over Spark. It is genuinely useful for porting existing pandas code, but
be honest about it in an interview: it has to fake an index, which introduces
shuffles that the equivalent Spark SQL would not have, and not everything is
implemented. It is a migration aid rather than the destination.

Note also `toPandas()` collects everything to the driver, so it is fine for a
final aggregated result and dangerous for anything else.

### Testing PySpark

```python
from pyspark.sql import SparkSession, functions as F

def add_total(df):
    """Pure transformation: DataFrame in, DataFrame out. This is the testable unit."""
    return df.withColumn("total", F.col("price") * F.col("qty"))

spark = SparkSession.builder.appName("test").master("local[2]").getOrCreate()

got = add_total(spark.createDataFrame([(10.0, 2)], ["price", "qty"]))
assert got.collect()[0]["total"] == 20.0
assert got.schema["total"].dataType.simpleString() == "double"
print("passed")
```

- **Write transformations as functions of DataFrame to DataFrame.** Keep
  `spark.read` and `df.write` in a thin edge layer so the logic is testable
  without I/O.
- **One session-scoped `local[2]` Spark session** as a pytest fixture. Session
  startup, not the assertions, dominates test time.
- **Set `spark.sql.shuffle.partitions` to a small number in tests**, or 200 empty
  partitions per shuffle will make the suite crawl.
- Compare with sorted `collect()` on small fixtures, or use
  `pyspark.testing.assertDataFrameEqual` (Spark 3.5+). **Never rely on row order**
  without an explicit `orderBy`.
- Test the schema, not just the values. Most production breakages are type and
  nullability changes.

### Common Gotchas

| Symptom | Cause |
| --- | --- |
| Job hangs with one straggler task | Data skew; try AQE skew join, broadcast, or salting |
| Driver OOM | `collect()` / `toPandas()`, or broadcasting something large |
| Thousands of tiny output files | `partitionBy` on high cardinality, or too many in-memory partitions at write |
| `coalesce(1)` made the whole job serial | No shuffle boundary; use `repartition(1)` instead |
| Join returned zero rows | Mismatched key types, or null keys in an inner join |
| Row count exploded after a join | Duplicated keys on one side |
| UDF is the bottleneck | Row-at-a-time Python UDF; use built-ins or `pandas_udf` |
| Same expensive chain computed twice | Two actions on an uncached lineage |
| `count()` differs between runs | Non-deterministic input ordering plus `limit`, or a `rand()` without a seed |
| Container killed, heap looked fine | Python worker / off-heap memory exceeded the overhead allowance |
| Everything slow, no hotspot | Small-files problem on input, or CSV instead of Parquet |

### Interview Summary

> I think about Spark in terms of partitions and shuffles, because that is where
> the time goes. A shuffle writes to disk, crosses the network and imposes a
> stage barrier, so my first questions on a slow job are how many `Exchange`
> nodes the plan has and whether the small side of each join is actually being
> broadcast. Parallelism is `min(partitions, cores)`, so the two classic failures
> are too few partitions leaving the cluster idle and skew leaving one task
> running after the other 199 finished. For skew I let AQE split the partition
> first, broadcast if the other side is small, and salt the hot key if not. On
> PySpark specifically, the thing that separates it from Scala Spark is the
> serialisation boundary: a row-at-a-time Python UDF is opaque to Catalyst and
> pays per-row serialisation, so I use built-in functions where they exist and a
> vectorised `pandas_udf` when they do not. I also want to say that reaching for
> Spark at all is a decision I would justify: under about 100 GB, DuckDB or
> Polars on one machine usually beats it on both wall clock and engineering time.

### References

- [PySpark documentation.](https://spark.apache.org/docs/latest/api/python/index.html)

- [Spark SQL performance tuning.](https://spark.apache.org/docs/latest/sql-performance-tuning.html)

- [Adaptive Query Execution.](https://spark.apache.org/docs/latest/sql-performance-tuning.html#adaptive-query-execution)

- [Structured Streaming programming guide.](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)

- [Apache Arrow and pandas UDFs in PySpark.](https://spark.apache.org/docs/latest/api/python/tutorial/sql/arrow_pandas.html)

- [Spark configuration reference.](https://spark.apache.org/docs/latest/configuration.html)
