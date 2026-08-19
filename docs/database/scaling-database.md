---
icon: material/trending-up
---

# Scaling Database

<a class="watch-video" href="https://www.youtube.com/watch?v=_1IKwnbscQU">&#9654;&nbsp;Watch Video</a>

### 1. Database Indexing

- Indexing work in the same way Book indexes work.

- B-Tree Index.

- Without Indexing even a simple search query can lead into a full table scan.

- Indexing increase read preformance but decrease the write preformance as indexes needs to be updated everytime a new data writes.

### 2. Materialized Views

- A materialized view, stores the results of a specific query as a physical table in the database.

- The data in the materialized view is precomputed and stored, meaning that the results are already available without the need to recompute the query each time the view is accessed.

- Materialized views must be refreshed periodically to make sure data is latest.

- Frequent data refresh can be expensive.

### 3. Denormalization

- Reduce Complex joins to improve query performance.

- Example: If we have a DB of a social media platform we can store users data directly into post table Facebook uses the same technique.

- Zerodha Also use Denormalization (Source: PGConf India 2023)

- Updates must be carefully manage to have consistency in the database.

### 4. Vertical Scaling

- Vertical scaling is the simplest technique of scaling.

- In vertical scaling we just increase the CPU, RAM or storage of the Server of the Database.

- Vertical scaling have hardware limitations and also cost ineffective.

- Single Point of failure.

### 5. Caching

- We can cache our frequently used data for faster processing.

- Caching can be implemented on various level like in memory Caching by using cache DB like Redis, Memchache or in Application level.

- We should manage chache refresh time (TTL) according to our use case carefully to make sure we are not serving old data to user always.

### 6. Horizontal Scaling

- Horizontal scaling can be done by sharding our data into multiple servers.

- Database Horizontal Scaling can according to two scenarios:

    - Read Heavy DB:

        - We can implement Replication.

        - A seperate server for replica DB which will be only used for Read operation.

        - This architecture is called master-slave archirecture.

        - Replication can be preformed in two ways Syncronous or Asyncronous.

    - Write Heave DB:

        - We can implement Database Partitioning/Sharding.

        - Partitioning is the technique to Split our DB into multiple small DB by using some hash funtion on ID.
