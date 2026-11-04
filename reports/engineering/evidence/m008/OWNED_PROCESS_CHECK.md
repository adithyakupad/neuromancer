The independent lifecycle assertion now queries ps only for the exact same recorded worker/
descendant PIDs it previously looked up in a whole-machine table. The PID absence/zombie
assertions remain identical, with an added process-query error check and2s bound. This avoids
retaining unrelated process-table entries if pytest introspection prints assertion values.
No production behavior, deadline or expected lifecycle outcome changes. Full tests and exact
final hosted source are requalified; earlier attempts remain separately identified.
