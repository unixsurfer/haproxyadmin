TODO
====

- Proper README file with instructions including haproxy example conf

- **FIXED** compare_results
  return type is not the same, is it a problem?
  d3a0f96 and 0bbe0f0 make sure we only work with integer numbers

- Test against hapee, haproxy-1.6dev1..

- *WORK in PROGRESS* Update docstring everywhere

- Investigate possible performance benefits when we filter 'show stats' cmd to
  list only frontend/backends/servers
