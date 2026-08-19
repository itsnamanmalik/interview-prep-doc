---
icon: material/sync-circle
---

# ACID Properties

<a class="watch-video" href="https://www.youtube.com/watch?v=GAe5oB742dw">&#9654;&nbsp;Watch Video</a>

ACID properties ensure that database transactions are reliable and maintain data integrity:

- Atomicity: A transaction is atomic, meaning it either completes in its entirety or not at all. If any part fails, the entire transaction returns to its original state.

- Consistency: The database remains consistent before and after the transaction. All constraints, rules, and relationships defined in the database are enforced during the transaction.

- Isolation: Each transaction is isolated from other transactions until it is completed. This ensures that the intermediate state of one transaction is invisible to other concurrent transactions.

- Durability: Once a transaction is committed, its changes are permanent and persist even in system failure. The changes are stored permanently in non-volatile memory (e.g., disk).
