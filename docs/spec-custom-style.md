# Spec: Private sqlfmt Fork — Custom House Style + De-forking

## Problem Statement

sqlfmt's default formatting style doesn't match the house SQL style the user wants for dbt models. The user wants a private fork of sqlfmt that:

- Produces SQL output in a specific, opinionated style (described below) instead of sqlfmt's defaults.
- No longer reads or presents as a public open-source project (community health files, changelog, branding) — it's a personal tool now, not something accepting outside contributions.

The user does not care how the formatter is implemented internally — only what the formatted output looks like. Implementation (parser, tree structure, CLI flags, etc.) is sqlfmt's existing machinery; this spec only constrains observable output.

## Solution

1. Strip the public-repo-specific files from the fork (CODE_OF_CONDUCT, CHANGELOG, CONTRIBUTING-equivalent, `.github/` issue/PR templates and CI badges tied to the upstream project identity) and rewrite the README to describe this as a personal fork. Keep LICENSE as-is (fork obligation).
2. Replace sqlfmt's formatting rules with the house style defined below, scoped to dbt model SQL (`select`-family statements only — no `insert`/`update`/`delete`/`merge` support required).

## User Stories

1. As the repo owner, I want the fork's README to describe my personal style tool, so that it no longer reads as an active open-source project soliciting contributions.
2. As the repo owner, I want CODE_OF_CONDUCT, CHANGELOG, and `.github/` community-health files removed, so that the repo doesn't carry artifacts implying public community process.
3. As a developer running the formatter on a dbt model, I want every major clause (`select`, `from`, `where`, `group by`, `having`, `order by`, `qualify`, `limit`, `union`/`union all`) separated from its neighbors by a blank line, so that each clause is visually distinct.
4. As a developer, I want a "trivial import CTE" (a CTE body that is exactly `select * from <single source>`) to stay on one line, so that boilerplate source-import CTEs don't bloat the file.
5. As a developer, I want every CTE — including trivial import CTEs — to have a blank line immediately after its opening `as (` and a blank line immediately before its closing `)`, so that CTE bodies are visually boxed off, regardless of whether the body itself is one line or many.
6. As a developer, I want the closing `)` of a CTE and its trailing comma glued together on one line (`),`), with a blank line separating that from the next CTE's name, so CTE boundaries are unambiguous.
7. As a developer, I want a dbt `config()` block at the top of a file formatted in the standard dbt multi-line style (`{{` on its own line, `config(` indented, each arg indented further with trailing comma, closing `)` and `}}` each on their own line), so config blocks look like idiomatic dbt.
8. As a developer, I want a blank line between the file's `config()` block and the `with` keyword, so the config is visually separated from the CTE chain.
9. As a developer, I want all SQL keywords and identifiers lowercase, so that the style matches modern dbt-community convention instead of legacy uppercase SQL.
10. As a developer, I want trailing commas (not leading commas) in column lists, `group by` lists, and value lists, so that the style matches traditional comma placement.
11. As a developer, I want a single-condition `where` or `having` clause to stay on the same line as the keyword (`where status = 'completed'`), so that trivial filters don't get needlessly split.
12. As a developer, I want multiple `where`/`having`/`on` conditions joined by `and`/`or` to stack on their own lines, each aligned under the first condition's indent, so that multi-condition filters are scannable.
13. As a developer, I want a single-column `group by` to stay on one line (`group by customer_id`), while a multi-column `group by` breaks each column onto its own indented line with trailing commas, so trivial grouping doesn't get needlessly split but complex grouping stays readable.
14. As a developer, I want table aliases written without `as` (`orders o`, not `orders as o`), while column aliases always use `as` (`order_total as total`), so that the two alias contexts are visually distinguishable.
15. As a developer, I want joins to always spell out `inner join` explicitly (never bare `join`), while `left join`/`right join` stay bare (never `left outer join`/`right outer join`), so that join type is always unambiguous without being verbose where redundant.
16. As a developer, I want a join's `on` condition to drop to its own line, indented under the join, so joins and their conditions are visually distinct from the table reference.
17. As a developer, I want multiple `on` conditions (join + `and`) to stack, aligned under the first `on` condition, matching the `where`-clause stacking rule.
18. As a developer, I want self-joins (same table, two aliases) formatted identically to any other join, with no special-cased treatment.
19. As a developer, I want a derived table (subquery in `from`) to follow the same universal blank-line-after-open-paren / blank-line-before-close-paren rule as other multi-line constructs, with its alias placed directly after the closing `)` and its `on` condition dropping to its own line below, same as a plain table join.
20. As a developer, I want `case` expressions formatted with `case` on its own line, each `when`/`else` indented 4 spaces under it, and `end [as alias]` back at `case`'s indent level.
21. As a developer, I want a simple `when ... then ...` with no `and`/`or` to stay on one line, unless that line exceeds the project's 100-character line length, in which case `then` drops to its own line indented one level deeper than `when`.
22. As a developer, I want any `when` condition containing `and`/`or` to always break out multi-line regardless of line length — the first condition stays on the `when` line, each subsequent `and`/`or` condition stacks on its own indented line, and `then` aligns with those `and`/`or` lines (one indent deeper than `when`, not back out to `when`'s own indent).
23. As a developer, I want a simple `case <expr> when <val> then ...` (as opposed to a searched `case when <condition> then ...`) to follow all the same rules, just with the expression on the `case` line.
24. As a developer, I want nested `case` expressions (a `case` inside another `case`'s `when`/`then`/`else`) to follow the exact same formatting rules recursively, with no flattening or special treatment.
25. As a developer, I want any multi-line construct (case expression, window function, subquery) that's wrapped inside a function call's parentheses (e.g. `sum(case ... end)`) to get a blank line immediately after the function's opening `(` and immediately before its closing `)`, same as the universal multi-line-wrap rule — with the single exception of a bare scalar-subquery wrapper (see story 32).
26. As a developer, I want window functions with a non-trivial `over (...)` (anything with `partition by`/`order by`/frame clause) to put each sub-clause (`partition by`, `order by`, `rows between ... and ...`) on its own line, indented under `over (`, with no blank line directly after `over (` or before its closing `)`.
27. As a developer, I want a fully trivial window function (`count(*) over ()`, no partition/order) to stay inline as a single line, since it has no multi-line content to box off.
28. As a developer, I want multiple window functions in the same `select` list to each get a blank line above and below, same as any other multi-line construct in a column list.
29. As a developer, I want `select distinct` to keep `distinct` glued to `select` on the same line.
30. As a developer, I want `qualify` (with a window-function predicate) to behave as its own top-level clause — blank-line-separated from neighboring clauses, with the window function body inside it following the normal window-function indentation rules.
31. As a developer, I want `limit` to be its own clause, blank-line-separated from what precedes it, with the value on the same line as `limit`.
32. As a developer, I want a scalar subquery wrapped in a bare `(...)` (e.g. in a `select` list) to have NO blank line directly after its opening `(` — the inner `select` drops right under it — while still having a blank line before the closing `)`. This is the one exception to story 25's universal open-paren blank-line rule; it applies only to this bare-paren scalar-subquery wrapper, not to `case`, `sum(`, `in (`, `exists (`, or derived-table parens.
33. As a developer, I want subqueries (in `where ... in (...)`, `where exists (...)`, derived tables, and scalar subqueries) to recursively follow every other rule in this spec internally — blank lines between their own inner `select`/`from`/`where`, same indentation rules, etc. — with no special-cased simplification for being "just a subquery."
34. As a developer, I want a parenthesized `or` group inside a `where` clause (e.g. `where (status = 'a' or status = 'b') and ...`) to stay on the `where` line itself, with subsequent `and` conditions dropping below as usual — the parenthesized group does not force its own line break.
35. As a developer, I want `union`/`union all`/`intersect`/`except` to sit at base indent (same level as `select`/`from`), with a blank line before and after.
36. As a developer, I want long function call argument lists (e.g. nested `coalesce(nullif(...), ...)`) that don't fit on one line to break each argument onto its own indented line with trailing comma and no blank-line boxing (since plain scalar args aren't clause-shaped) — while a version that fits within 100 characters stays on one line.
37. As a developer, I want a long `in (...)` value list to break one literal value per line with trailing comma and no blank-line boxing, while a short list that fits in 100 characters stays on one line.
38. As a developer, I want long arithmetic/expression lines that exceed 100 characters to break with the operator (`+`, `-`, etc.) leading the continuation line, indented under the expression's start.
39. As a developer, I want `cast(x as type)` to always stay inline as a single unit, never broken across lines regardless of surrounding context.
40. As a developer, I want comments (`--` and `/* */`) left exactly as the author wrote them — no repositioning, no reformatting, no enforced placement rules — since comment placement is an authorial choice the formatter shouldn't override.
41. As a developer, I want no semicolons anywhere in formatted output (dbt models are single bare statements).
42. As a developer, I want the formatter to apply a 100-character line-length limit as the trigger for every "does this need to break onto multiple lines" decision described above.

## Implementation Decisions

- Scope: `select`-family dbt model SQL only. `insert`/`update`/`delete`/`merge` are out of scope and need no formatting rules.
- Line length: 100 characters is the universal threshold that decides whether a construct collapses to one line or breaks out, wherever "fits on one line" is referenced above.
- The "blank line before/after a multi-line construct" behavior is a single general rule applied consistently everywhere a multi-line sub-construct (case, window function, subquery, CTE body, config block, nested case, join's derived table) appears — with exactly one documented exception: the bare `(...)` scalar-subquery wrapper, which omits the blank line after its opening `(` only.
- Repo-identity changes: remove `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, `.github/` issue/PR templates and workflow badges tied to upstream project identity; rewrite `README.md`; keep `LICENSE` unchanged.
- No new modules/interfaces are prescribed by this spec — it describes target output only. Whoever implements this against sqlfmt's existing formatting engine decides how to wire these rules into its internals (lexer/parser/node tree/printer).

## Testing Decisions

- Tests should assert on formatted *output* (golden-file / snapshot style: input SQL in, expected formatted SQL out), not on internal formatter implementation details (node types, tree shape).
- Cover each user story above with at least one golden-file case; many stories compose (e.g. a nested `case` inside a `sum()` inside a CTE) — include at least a few composed/nested cases, not just isolated single-rule cases, since that's where the examples in this spec's derivation process actually surfaced bugs.
- Prior art: sqlfmt's existing test suite already uses golden-file fixtures (`tests/data/` style input/expected pairs per upstream); follow that existing pattern rather than introducing a new test style.

## Out of Scope

- `insert`/`update`/`delete`/`merge`/DDL statement formatting.
- Any YouTube-sourced or other external example corpus — the rules above were derived directly through user-reviewed examples, not scraped video content.
- Publishing/distributing this fork publicly, accepting outside contributions, or any CI/release automation tied to the upstream project's public-facing process.
- Backward compatibility with sqlfmt's own default style or any config flag to toggle between styles — this fork has one style.

## Further Notes

This spec was derived by presenting the user with incrementally complex SQL examples (basic clauses → joins → CTEs → config blocks → case expressions → window functions → subqueries → set operations → casts/operators/comments) and having the user correct each one until confirmed, rather than by consulting external references. The two most-corrected areas during derivation were: (1) blank lines are required between *every* clause, not just a line break — this was missed repeatedly early on — and (2) the universal "blank line after open-paren / before close-paren for multi-line constructs" rule, which has exactly one carved-out exception (bare scalar-subquery parens).
