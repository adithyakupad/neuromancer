# Personal coding style for V2

The primary observations come from the retained page renders of the
submitted Georgia Tech CS 1371 Exam 2, inspected during M017. The
original PDF was absent at its former Downloads path. The earlier
style guide provides provenance for the renders. No exam pages,
solutions or identifiers are distributed with this candidate.

| Submission evidence | Python convention |
|---|---|
| sweetCombo, PDF p20 | Initialize decision flags, name predicates and combine the decisions at the end. |
| getCar, p24 | Separate the search from output construction. Use a bounded loop or direct indexing. |
| exitStrategy, pp40–41 | Give each decision a name and collect decisions in an ordered mask. |
| boxInventory, p45 | Separate metadata and numeric data, name columns, vectorize the calculation and apply one sorting permutation. |

The examples show a preference for explicit stages. Preserve it
without carrying forward unbounded loops, index reuse between scans,
one-based indexing or repeated string growth. Type hints and snake_case
are Python conventions. Generated code is not attributed to the student.

Keep an algorithm's validation, mathematical update and publication
separate. Use meaningful local names and retain conventional symbols
when they clarify an equation. Preserve array layout and evaluation
order. Explain units, shapes, causal boundaries and failure states.
Use vectorized NumPy where it expresses the operation directly.

The previous four-module branch is an unqualified reference. M017
uses fresh changes from the integrated baseline and keeps its style
review independent of release packaging and reliability changes.
