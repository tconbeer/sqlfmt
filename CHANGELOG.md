# sqlfmt CHANGELOG

All notable changes to this project will be documented in this file.

## [Unreleased]

### Features

-   Add support for formatting SQL code blocks in Markdown files. Introduces a new extra install (`pipx install shandy-sqlfmt[markdownfmt]`) and CLI option (`--no-markdownfmt`) ([#593](https://github.com/tconbeer/sqlfmt/issues/593) - thank you, [@michael-the1](https://github.com/michael-the1)).

## [0.21.4] - 2024-07-09

### Formatting Changes and Bug Fixes

- Databricks `left anti` & `right anti` joins are now supported.

## [0.21.3] - 2024-04-25

### Bug Fixes

- The Postgres operators for `(NOT) (I)LIKE`, `~~`, `~~*`, `!~~`, `!~~*`, are now supported (these use two tildes where the posix version of these operators use a single tilde) ([#576](https://github.com/tconbeer/sqlfmt/issues/576) - thank you [@tuckerrc](https://github.com/tuckerrc)!).

## [0.21.2] - 2024-01-22

### Bug Fixes

- `{% for %}...{% else %}...{% endfor %}` loops are now supported. Previously, a BracketError was raised if a `for` loop included an `else` tag ([#549](https://github.com/tconbeer/sqlfmt/issues/549) - thank you, [@yassun7010](https://github.com/yassun7010)!).

## [0.21.1] - 2023-12-19

### Bug Fixes

- Fixes a bug where extra indentation was added inside multiline jinja tags if those jinja tags contained a python multiline string ([#536](https://github.com/tconbeer/sqlfmt/issues/500) - thank you [@yassun7010](https://github.com/yassun7010)!).

## [0.21.0] - 2023-10-20

### Bug Fixes

- Adds support for the `map<...>` type declaration syntax from Athena. ([#500](https://github.com/tconbeer/sqlfmt/issues/500) - thank you for the issue and fix, [@benjamin-awd](https://github.com/benjamin-awd)!)
- Fixes a bug where nested dicts inside jinja expressions (e.g., `{{ {'a': {'b': 1}} }}`) could cause parsing errors ([#471](https://github.com/tconbeer/sqlfmt/issues/500) - thank you [@rparvathaneni-sc](https://github.com/rparvathaneni-sc) and [@benjamin-awd](https://github.com/benjamin-awd)!). This fix introduces a dependency on jinja2 > v3.0.
- Fixes a bug in the lexing logic that prevented the walrus operator (`:=`) from being lexed as a single token ([#502](https://github.com/tconbeer/sqlfmt/issues/502) - thank you [@federico-hero](https://github.com/federico-hero)!).

## [0.20.0] - 2023-09-25

### BREAKING CHANGES

- Drops support for Python 3.7. Please upgrade to Python 3.8 or higher.

### Formatting Changes and Bug Fixes

- `any()` and `all()` will no longer get spaces between the function name and the parenthesis, unless they are a part of a `like any ()` or `like all ()` operator ([#483](https://github.com/tconbeer/sqlfmt/issues/483) - thank you [@damirbk](https://github.com/damirbk)!).
- Snowflake's `//` comment markers are now parsed as comments and rewritten to `--` on formatting ([#468](https://github.com/tconbeer/sqlfmt/issues/468) - thank you [@nilsonavp](https://github.com/nilsonavp)!).
- DuckDB's `semi`, `anti`, `positional`, and `asof` joins are now supported. ([#482](https://github.com/tconbeer/sqlfmt/issues/482)).

## [0.19.2] - 2023-07-31

### Bug Fixes

- Fixes a bug where `--exclude` would not follow symlinks when globbing
  ([#457](https://github.com/tconbeer/sqlfmt/issues/457) - thank you [@jeancochrane](https://github.com/jeancochrane)!).

## [0.19.1] - 2023-07-13

### Bug Fixes

- Fixes a bug where `--fmt: off` comments could cause an error in formatting a file
  ([#447](https://github.com/tconbeer/sqlfmt/issues/447) - thank you [@ramonvermeulen](https://github.com/ramonvermeulen)!).
- Fixes a bug where some formatting changes were applied to sections of code in
  `--fmt: off` blocks.
- Fixes a bug where comments inside of `--fmt: off` would still be formatted.
  ([#136](https://github.com/tconbeer/sqlfmt/issues/136)).

## [0.19.0] - 2023-06-08

### Bug Fixes

- Relative `exclude` paths defined in `pyproject.toml` files are now evaluated relative to the location of the file, not the current working directory.
  Relative paths provided to the `--exclude` option (or env var) are evaluated relative to the current working directory. Files and exclude paths
  are now compared as resolved, absolute paths. (Fixes [#431](https://github.com/tconbeer/sqlfmt/issues/431) - thank you [@cmcnicoll](https://github.com/cmcnicoll)!)
- Fixes a bug where a comment like `{#-- comment --#}` would cause a false positive for the
  comment safety check. ([#434](https://github.com/tconbeer/sqlfmt/issues/434))

### Formatting Changes

- sqlfmt now supports the `<=>` operator ([#432](https://github.com/tconbeer/sqlfmt/issues/432) - thank you [@kathykwon](https://github.com/kathykwon)!)

## [0.18.3] - 2023-05-31

### Bug Fixes

- fixes a bug where multiple c-style comments (e.g., `/* comment */`) on a single line would cause sqlfmt
  to not include all comments in formatted output ([#419](https://github.com/tconbeer/sqlfmt/issues/419) - thank you [@aersam](https://github.com/aersam)!)

### Features

- adds a safety check to ensure comments are preserved in formatted output

## [0.18.2] - 2023-05-31

- fixes a bug where specifying both relative and absolute paths would cause sqlfmt to crash ([#426](https://github.com/tconbeer/sqlfmt/issues/426) - thank you for the issue and fix, [@smcgivern](https://github.com/smcgivern)!)

## [0.18.1] - 2023-05-10

- fixes a bug when lexing `union distinct` tokens ([#417](https://github.com/tconbeer/sqlfmt/issues/417) - thank you, [@paschmaria](https://github.com/paschmaria)!)

## [0.18.0] - 2023-04-19

### Formatting Changes

- the contents of jinja blocks are now indented if the block wraps onto multiple rows ([#403](https://github.com/tconbeer/sqlfmt/issues/403)). This is now the proper sqlfmt style:

  ```sql
  select
      some_field,
      {% for some_item in some_sequence %}
          some_function({{ some_item }}){% if not loop.last %}, {% endif %}
      {% endfor %}
  ```

  While in this simple example the new style makes it less clear 
  that `some_field` and `some_function` are at the
  same SQL depth, the formatting of complex files with nested jinja blocks is much improved.
  For example:

  ```sql
  {%- for col in cols -%}
      {%- if col.column.lower() not in remove | map(
          "lower"
      ) and col.column.lower() not in exclude | map("lower") -%}
          {% do include_cols.append(col) %}
      {%- endif %}
  {%- endfor %}
  ```

  See also [this discussion](https://github.com/tconbeer/sqlfmt/discussions/317). Thank you 
  [@dave-connors-3](https://github.com/dave-connors-3) and 
  [@alrocar](https://github.com/alrocar)!
- sqlfmt now supports all [Postgres frame clauses](https://www.postgresql.org/docs/current/sql-expressions.html#SYNTAX-WINDOW-FUNCTIONS), not just those that start with `rows between`. ([#404](https://github.com/tconbeer/sqlfmt/issues/404))

## [0.17.1] - 2023-04-12

### Bug Fixes

- fixed a bug where format-off tokens could cause sqlfmt to raise a bracket mismatch error ([#395](https://github.com/tconbeer/sqlfmt/issues/395) - thank you, [@AndrewLaneAtPowerSchool](https://github.com/AndrewLaneAtPowerSchool)!).

## [0.17.0] - 2023-02-24

### Features

- sqlfmt now defaults to reading and writing files using the `utf-8` encoding. Previously, we used Python's default behavior of using the encoding from the host machine's locale. However, as `utf-8` becomes a de-facto standard, this was causing issues for some Windows users, whose locale was set to use older encodings. You can use the `--encoding` option to specify a different encoding. Setting encoding to `inherit`, e.g., `sqlfmt --encoding inherit foo.sql` will revert to the old behavior of using the host's locale. sqlfmt will detect and preserve a UTF BOM if it is present. If you specify `--encoding utf-8-sig`, sqlfmt will always write a UTF-8 BOM in the formatted file. ([#350](https://github.com/tconbeer/sqlfmt/issues/350), [#381]((https://github.com/tconbeer/sqlfmt/issues/381)), [#383]((https://github.com/tconbeer/sqlfmt/issues/383)) - thank you [@profesia-company](https://github.com/profesia-company), [@cmcnicoll](https://github.com/cmcnicoll), [@aersam](https://github.com/aersam), and [@ryanmeekins](https://github.com/ryanmeekins)!)

## [0.16.0] - 2023-01-27

### Formatting Changes + Bug Fixes

- sqlfmt no longer merges lines that contain comments, unless the position of those comments can be preserved ([#348](https://github.com/tconbeer/sqlfmt/issues/348) - thank you, [@rileyschack](https://github.com/rileyschack) and [@IanEdington](https://github.com/IanEdington)!). Accordingly, comments that are inline will stay inline, even if they are too long to fit.
- sqlfmt no longer merges together lines containing multiline jinja blocks unless those lines start with an operator or comma ([#365](https://github.com/tconbeer/sqlfmt/issues/365) - thank you, [@gavlt](https://github.com/gavlt)!).
- fixed a bug where adding a jinja end tag (e.g., `{% endif %}`) to a line could cause bad formatting of everything on that line

## [0.15.2] - 2023-01-23

### Features

- adds support for ARM-based platforms using Docker.

## [0.15.1] - 2023-01-20

### Features

- added a Dockerfile for running sqlfmt in a container. New versions of sqlfmt will include Docker builds pushed to the GitHub Container Registry (thank you [@ysmilda](https://github.com/ysmilda)!).

## [0.15.0] - 2023-01-18

### Formatting Changes + Bug Fixes

- sqlfmt now removes extra blank lines ([#249](https://github.com/tconbeer/sqlfmt/issues/313) - thank you, [@nfcampos](https://github.com/nfcampos)!). Basically, no more than 1 blank line inside queries or blocks; no more than 2 between queries or blocks.
- sqlfmt now supports `create <object> ... clone` statements ([#313](https://github.com/tconbeer/sqlfmt/issues/313)).
- sqlfmt will now format all files that end with `*.sql` and `*.sql.jinja`, even those with other dots in their filenames ([#354](https://github.com/tconbeer/sqlfmt/issues/354) - thank you [@ysmilda](https://github.com/ysmilda)!).
- fixed a bug where `{% call %}` blocks with arguments like `{% call(foo) bar(baz) %}` would cause a parsing error ([#353](https://github.com/tconbeer/sqlfmt/issues/353) - thank you [@IgnorantWalking](https://github.com/IgnorantWalking)!).
- sqlfmt now supports [bun placeholders](https://bun.uptrace.dev/guide/placeholders.html) ([#356](https://github.com/tconbeer/sqlfmt/issues/356) - thank you [@ysmilda](https://github.com/ysmilda)!)

### Features

- by default, sqlfmt now runs an additional safety check that parses the formatted output to ensure it contains all of the same content as the raw input. This incurs a slight (~20%) performance penalty. To bypass this safety check, you can use the command line option `--fast`, the corresponding TOML or environment variable config, or pass `Mode(fast=True)` to any API method. The safety check is automatically bypassed if sqlfmt is run with the `--check` or `--diff` options. If the safety check fails, the CLI will include an error in the report, and the `format_string` API will raise a `SqlfmtEquivalenceError`, which is a subclass of `SqlfmtError`.

## [0.14.3] - 2023-01-05

### Formatting Changes + Bug Fixes

- fixed a bug where very long lines could raise `RecursionError` ([#343](https://github.com/tconbeer/sqlfmt/issues/343) - thank you [@kcem-flyr](https://github.com/kcem-flyr)!).

## [0.14.2] - 2022-12-12

### Formatting Changes + Bug Fixes

- fixed a bug where nested `{% set %}` and `{% call %}` blocks would cause a parsing error ([#338](https://github.com/tconbeer/sqlfmt/issues/338) - thank you [@AndrewLane](https://github.com/AndrewLane)!).

## [0.14.1] - 2022-12-06

### Formatting Changes + Bug Fixes

- sqlfmt now supports `is [not] distinct from` as a word operator ([#327](https://github.com/tconbeer/sqlfmt/issues/327) - thank you [@IgnorantWalking](https://github.com/IgnorantWalking), [@kadekillary](https://github.com/kadekillary)!).
- fixed a bug where jinja `{% call %}` blocks that called a macro that wasn't `statement` caused a parsing error ([#335](https://github.com/tconbeer/sqlfmt/issues/335) - thank you [@AndrewLane](https://github.com/AndrewLane)!).

### Performance

- sqlfmt runs finish in 20% less time due to algorithmic improvements

## [0.14.0] - 2022-11-30

### Formatting Changes + Bug Fixes

- sqlfmt now supports `{% materialization ... %}` and `{% call statement(...) %}` blocks ([#309](https://github.com/tconbeer/sqlfmt/issues/309)).
- sqlfmt now resets the SQL depth of a query after encountering an `{% endmacro %}`, `{% endtest %}`, `{% endcall %}`, or `{% endmaterialization %}` tag.
- sqlfmt now supports `create warehouse` and `alter warehouse` statements ([#312](https://github.com/tconbeer/sqlfmt/issues/312), [#299](https://github.com/tconbeer/sqlfmt/issues/312)).
- sqlfmt now supports `alter function` and `drop function` statements ([#310](https://github.com/tconbeer/sqlfmt/issues/310), [#311](https://github.com/tconbeer/sqlfmt/issues/311)), and Snowflake's `create external function` statements ([#322](https://github.com/tconbeer/sqlfmt/issues/322)).
- sqlfmt better supports numeric constants (number literals), including those using scientific notation (e.g., `1.5e-9`) and the unary `+` or `-` operators (e.g., `+3`), and is now smarter about when the `-` symbol is the unary negative or binary subtraction operator. ([#321](https://github.com/tconbeer/sqlfmt/issues/321) - thank you [@liaopeiyuan](https://github.com/liaopeiyuan)!).
- fixed a bug where we added extra whitespace to the end of empty comment lines ([#319](https://github.com/tconbeer/sqlfmt/issues/319) - thank you [@eherde](https://github.com/eherde)!).
- fixed an bug where wrapping unsupported DDL in jinja would cause a parsing error ([#326](https://github.com/tconbeer/sqlfmt/issues/326) - thank you [@ETG-msimons](https://github.com/ETG-msimons)!). Also improved parsing of unsupported DDL and made false positives less likely.
- fixed a bug where we could have unsafely run _black_ against jinja that contained Python keywords and their safe alternatives (e.g., `return(return_())`).
- fixed a bug where we deleted some extra whitespace lines (and in very rare cases, nonblank lines)
- fixed a bug where Python recursion limits could cause incorrect formatting in rare cases

## [0.13.0] - 2022-11-01

### Formatting Changes + Bug Fixes

- sqlfmt now supports `delete` statements and the associated keywords `using` and `returning` ([#281](https://github.com/tconbeer/sqlfmt/issues/281)).
- sqlfmt now supports `grant` and `revoke` statements and all associated keywords ([#283](https://github.com/tconbeer/sqlfmt/issues/283)).
- sqlfmt now supports `create function` statements and all associated keywords ([#282](https://github.com/tconbeer/sqlfmt/issues/282)).
- sqlfmt now supports the `explain` keyword ([#280](https://github.com/tconbeer/sqlfmt/issues/280)).
- sqlfmt now supports BigQuery typed table and struct definitions and literals, like `table<a int64, b bytes(5), c string>`.
- sqlfmt now supports variables like `$foo` as ordinary identifiers.

### Features

- sqlfmt is now tested against Python 3.11 ([#242](https://github.com/tconbeer/sqlfmt/issues/242)). Previous versions of sqlfmt are also compatible.
  with Python 3.11. When installed in 3.11, sqlfmt no longer requires the `tomli` dependency.

## [0.12.0] - 2022-10-14

### Formatting Changes + Bug Fixes

- DDL and DML statements (`create`, `insert`, `grant`, etc.) will no longer be formatted ([#243](https://github.com/tconbeer/sqlfmt/issues/243)). 
  These statements were never supported by sqlfmt, and the existing algorithm produced bad formatting. Support for DDL and DML statements will be gradually added back in in future versions.
  For more information, see the [tracking issue for DDL support](https://github.com/tconbeer/sqlfmt/issues/262).
- BigQuery typed array literals like `array<float64>[1, 2]` are now supported, and spaces will no longer be inserted around `<` and `>` ([#212](https://github.com/tconbeer/sqlfmt/issues/212)).
- SparkSQL-specific keywords `tablesample`, `cluster by`, `distribute by`, `sort by`, and `lateral view` are now supported by the polyglot dialect ([#264](https://github.com/tconbeer/sqlfmt/issues/264)).
- `pivot` and `unpivot` are now supported as word operators, and will have a space between the keyword and the following parentheses.
- `values` is now supported as an unterminated keyword; tuples of values will be indented from the `values` keyword if they span more than one line ([#263](https://github.com/tconbeer/sqlfmt/issues/263)).

## [0.11.1] - 2022-09-17

### Features

- Any CLI option can now be configured using environment variables. Variable names are prefixed by `SQLFMT` and are the `SHOUTING_CASE` spelling of the options. For example, `sqlfmt . --line-length 100` is equivalent to `SQLFMT_LINE_LENGTH=100 sqlfmt .` ([#251](https://github.com/tconbeer/sqlfmt/issues/251)).

### Documentation

- The README has been shortened and now links to [docs.sqlfmt.com](https://docs.sqlfmt.com).

## [0.11.0] - 2022-08-21

### Breaking API Changes

- The `files` argument of `api.run` is now a `Collection[pathlib.Path]` that represents an exact collection of files to be formatted, instead of a list of paths to search for files. Use `api.get_matching_paths(paths, mode)` to return the set of exact paths expected by `api.run`.

### Features

- sqlfmt will now display a progress bar for long runs ([#231](https://github.com/tconbeer/sqlfmt/pull/231)). You can disable this with the `--no-progressbar` option.
- `api.run` now accepts an optional `callback` argument, which must be a `Callable[[Awaitable[SqlFormatResult]], None]`. Unless the `--single-process` option is used, the callback is executed after each file is formatted.
- sqlfmt can now be called as a python module, with `python -m sqlfmt`.

### Formatting Changes + Bug Fixes

- adds more granularity to operator precedence and will merge lines more aggressively that start with high-precedence operators ([#200](https://github.com/tconbeer/sqlfmt/issues/200)).
- improves the formatting of `between ... and ...`, especially in situations where the source includes a line break ([#207](https://github.com/tconbeer/sqlfmt/issues/207)).
- improves the consistency of formatting long chains of operators that include parentheses ([#214](https://github.com/tconbeer/sqlfmt/issues/214)).
- fixes a bug that caused unnecessary copying of the cache when using multiprocessing. Large projects should see dramatically faster (near-instant) runs once the cache is warm.
- fixes a bug that could cause lines with long jinja tags to be one character over the line length limit, and could result in unstable formatting ([#237](https://github.com/tconbeer/sqlfmt/issues/237) - thank you [@nfcampos](https://github.com/nfcampos)!).
- fixes a bug that formatted array literals like they were indexing operations ([#235](https://github.com/tconbeer/sqlfmt/issues/235) - thank you [@nfcampos](https://github.com/nfcampos)!).

## [0.10.1] - 2022-08-05

### Features

- sqlfmt now supports the psycopg placeholders `%s` and `%(name)s` ([#198](https://github.com/tconbeer/sqlfmt/issues/198) - thank you [@snorkysnark](https://github.com/snorkysnark)!).

### Formatting Changes + Bug Fixes

- sqlfmt now standardizes whitespace inside word tokens ([#201](https://github.com/tconbeer/sqlfmt/issues/201)).
- `using` is now treated as a word operator. It gets a space before its brackets and merging with surrounding lines is now much improved ([#218](https://github.com/tconbeer/sqlfmt/issues/218) - thank you [@nfcampos](https://github.com/nfcampos)!).
- `within group` and `filter` are now treated like `over`, and the formatting of those aggregate clauses is improved ([#205](https://github.com/tconbeer/sqlfmt/issues/205)).

## [0.10.0] - 2022-08-02

### Features

- sqlfmt now supports ClickHouse. When run with the `--dialect clickhouse` option, sqlfmt will not lowercase names that could be case-sensitive in ClickHouse, like function names, aliases, etc. ([#193](https://github.com/tconbeer/sqlfmt/issues/193) - thank you [@Shlomixg](https://github.com/Shlomixg)!).

### Formatting Changes + Bug Fixes

- formatting for chained boolean operators with complex expressions is now significantly improved ([#189](https://github.com/tconbeer/sqlfmt/issues/189) - thank you [@Rainymood](https://github.com/Rainymood)!).
- formatting for array indexing is now significantly improved ([#209](https://github.com/tconbeer/sqlfmt/issues/209)) and sqlfmt no longer inserts spaces between the `offset()` function and its brackets.
- set operators (like `union`) are now formatted differently. They must be on their own line, and will not cause subsequent blocks to be indented ([#188](https://github.com/tconbeer/sqlfmt/issues/188) - thank you [@Rainymood](https://github.com/Rainymood)!).
- `select * except (...)` syntax is now explicitly supported, and formatting is improved. Support added for BigQuery and DuckDB star options: `except`, `exclude`, `replace`.
- sqlfmt no longer inserts spaces between nested or repeated brackets, like `(())` or `()[]`.
- a bug causing unstable formatting with long/multiline jinja tags has been fixed ([#175](https://github.com/tconbeer/sqlfmt/issues/175)).

## [0.9.0] - 2022-06-02

### Features

- jinjafmt is now able to format jinja that contains functions and variables that are reserved python words (e.g., return, except, from) ([#177](https://github.com/tconbeer/sqlfmt/issues/177), [#155](https://github.com/tconbeer/sqlfmt/issues/155)), and `~`, the jinja string concatenation operator ([#182](https://github.com/tconbeer/sqlfmt/issues/182))
- adds a new command-line option to reset the sqlfmt cache ([#184](https://github.com/tconbeer/sqlfmt/issues/184))

### Fixes

- fixes issue where jinjafmt would insert a trailing comma into multiline macro definitions, causing dbt compiling errors ([#156](https://github.com/tconbeer/sqlfmt/issues/156))
- fixes issue causing unstable formatting of multiline jinja tags when black is unable to parse the tag ([#176](https://github.com/tconbeer/sqlfmt/issues/176))
- fixes issue for developers where pre-commit hooks would not install

### Primer

- sqlfmt_primer now runs against forked (formatted) repos to make changes easier to detect

## [0.8.0] - 2022-05-04

### Formatting Changes

- sqlfmt is now more conservative about preserving whitespace around jinja expressions when we remove newlines ([#162](https://github.com/tconbeer/sqlfmt/issues/162), [#165](https://github.com/tconbeer/sqlfmt/issues/165) - thank you [@rcaddell](https://github.com/rcaddell) and [@rjay98](https://github.com/rjay98)!)
- jinja blocks are now dedented before line merging, instead of after. This results in small changes to formatted output in some cases where jinja blocks are used
- fixes an issue where jinja else and elif statements could cause unstable formatting. May impact whitespace for the tokens following `{% else %}` and `{% elif %}` statements

## [0.7.0] - 2022-04-24

### Breaking Changes

- api.run now accepts `files` as a `List[pathlib.Path]` instead of a `List[str]`

### Features

- any command line option can now be set in a `pyproject.toml` file. See `README` for more information ([#90](https://github.com/tconbeer/sqlfmt/issues/90))
- sqlfmt now accepts an `--exclude` option to specify a glob of files to exclude from formatting ([#131](https://github.com/tconbeer/sqlfmt/issues/131))

## [0.6.0] - 2022-03-21

### Formatting Fixes

- adds support for snapshot blocks, so the contents of those blocks are now properly formatted ([#137](https://github.com/tconbeer/sqlfmt/issues/137))
- fixes issue causing unstable formatting of multiline jinja tags when black is not installed ([#138](https://github.com/tconbeer/sqlfmt/issues/138))
- fixes formatting of semicolons and semicolon-delimited queries ([#132](https://github.com/tconbeer/sqlfmt/issues/132))

## [0.5.1] - 2022-02-08

### Fixes

- adds support for numbered field references (e.g., `$1`) and snowflake stages (`@my_stage`) as identifiers
- do not split lines before the `between` operator's `and` keyword ([#124](https://github.com/tconbeer/sqlfmt/issues/124) - thank you [@WestComputing](https://github.com/WestComputing)!)

## [0.5.0] - 2022-02-02

### Formatting changes

- formats the contents of jinja tags (the code between the curlies) using _black_, the Python formatter. If _black_ is not already installed, you can use this feature by re-installing sqlfmt with the jinjafmt extra (`pipx install sqlfmt[jinjafmt]`). If _black_ is installed, but you do not want to use this feature, you can disable it with the command-line option `--no-jinjafmt`
- no longer inserts spaces around colons ([#103](https://github.com/tconbeer/sqlfmt/issues/103) - thank you [@noel](https://github.com/noel)!)

### Fixes

- adds "cross join" to list of supported join types. No longer merges the "cross" keyword with the previous statement ([#110](https://github.com/tconbeer/sqlfmt/issues/110) - thank you [@rdeese](https://github.com/rdeese)!)
- adds support for every valid operator in postgresql, even the weird ones, like `@>`, `||/`, `?-|` ([#105](https://github.com/tconbeer/sqlfmt/issues/105))

## [0.4.3] - 2022-01-31

### Fixes

- removes an unnecessary dependency on black that broke installation ([#98](https://github.com/tconbeer/sqlfmt/issues/98) - thank you [@ljhopkins2](https://github.com/ljhopkins2)!)

## [0.4.2] - 2022-01-26

### Features

- adds an option, `--single-process`, to force single-processing, even when formatting many files

### Under the Hood

- when formatting multiple files, uses multiprocessing for ~3x faster throughput

## [0.4.1] - 2022-01-20

### Formatting changes

- preserves leading and trailing blank lines when merging lines with content
- no longer prints whitespace on blank lines

## [0.4.0] - 2022-01-20

### Formatting changes

- adds special support for jinja, with new formatting rules for jinja statements, expressions, and blocks
- safely standardizes whitespace around jinja statements and expressions
- merges lines within and across jinja blocks while balancing start/end statements
- jinja block tags can no longr be indented farther than any of their contents

### Features

- developers can now easily profile sqlfmt performance (after installing the sqlfmt_primer extra) with `make profiling`

### Fixes

- no longer fails with a parsing error if "end" is used as a name in the query

### Under the Hood

- refactors lexing using typical callable architecture for more flexibility
- adds new token types for jinja statements and blocks
- refactors calculation of node and line depth to include jinja blocks
- adds some caching to line properties for performance enhancements

## [0.3.0] - 2021-12-16

### Formatting changes

- refactors comment parsing for improved formatting of comments and merging around comments
- standardizes comments and splits long comments onto multiple lines if necessary
- improves splitting and merging of lines with operators (like "+", "as", "on", etc.)
- improves formatting of queries that use leading commas
- improves merging of statements with chained brackets ("( something ) + ( something_else )" )

### Features

- adds a simple cache and skips formatting files that have not changed since last successful run
- improves the welcome message displayed when running sqlfmt with no arguments

### Fixes

- supports all postgres and bigquery string literals and quoted identifiers, including triple quotes, escaped quotes, dollar-delimited, etc.
- no longer fails with a parsing error when encountering a semicolon
- properly delineates between "\*" as "all fields" and as the multiplication operator

## [0.2.1] - 2021-12-04

### Performance

- refactors line splitting algorithm and creating a line from nodes; provides 3x speedup of sqlfmt (now formats roughly 100 files/sec)

### Fixes

- refactored lexer for better parsing of tokens on multiple lines

## [0.2.0] - 2021-11-16

### Features

- can format text through stdin by passing `-` as the files argument
- supports `--quiet` option
- supports `-- fmt: off` and `-- fmt: on` comments in sql files
- supports more select keywords, like `window` and `qualify`
- supports back-ticks for quoting relation names
- supports MySQL-style comments (`# comment`)
- adds a new cli tool, sqlfmt_primer, to run sqlfmt against known OSS projects to gauge changes

### Fixes

- fixes parsing of jinja tags (use lazy regex so we don't match multiple tags at once)
- fixes issue with whitespace around jinja tags
- fixes capitalization of word operators (on, and, etc.)
- fixes parsing error caused by comments without leading spaces

## [0.1.0] - 2021-11-08

### Features

- initial release
- discovers .sql and .sql.jinja files
- formats the files it discovers
- supports --check and --diff options
- supports --no-color

[unreleased]: https://github.com/tconbeer/sqlfmt/compare/0.21.4...HEAD
[0.21.4]: https://github.com/tconbeer/sqlfmt/compare/0.21.3...0.21.4
[0.21.3]: https://github.com/tconbeer/sqlfmt/compare/0.21.2...0.21.3
[0.21.2]: https://github.com/tconbeer/sqlfmt/compare/0.21.1...0.21.2
[0.21.1]: https://github.com/tconbeer/sqlfmt/compare/0.21.0...0.21.1
[0.21.0]: https://github.com/tconbeer/sqlfmt/compare/0.20.0...0.21.0
[0.20.0]: https://github.com/tconbeer/sqlfmt/compare/0.19.2...0.20.0
[0.19.2]: https://github.com/tconbeer/sqlfmt/compare/0.19.1...0.19.2
[0.19.1]: https://github.com/tconbeer/sqlfmt/compare/0.19.0...0.19.1
[0.19.0]: https://github.com/tconbeer/sqlfmt/compare/0.18.3...0.19.0
[0.18.3]: https://github.com/tconbeer/sqlfmt/compare/0.18.2...0.18.3
[0.18.2]: https://github.com/tconbeer/sqlfmt/compare/0.18.1...0.18.2
[0.18.1]: https://github.com/tconbeer/sqlfmt/compare/0.18.0...0.18.1
[0.18.0]: https://github.com/tconbeer/sqlfmt/compare/0.17.1...0.18.0
[0.17.1]: https://github.com/tconbeer/sqlfmt/compare/0.17.0...0.17.1
[0.17.0]: https://github.com/tconbeer/sqlfmt/compare/0.16.0...0.17.0
[0.16.0]: https://github.com/tconbeer/sqlfmt/compare/0.15.2...0.16.0
[0.15.2]: https://github.com/tconbeer/sqlfmt/compare/0.15.1...0.15.2
[0.15.1]: https://github.com/tconbeer/sqlfmt/compare/0.15.0...0.15.1
[0.15.0]: https://github.com/tconbeer/sqlfmt/compare/0.14.3...0.15.0
[0.14.3]: https://github.com/tconbeer/sqlfmt/compare/0.14.2...0.14.3
[0.14.2]: https://github.com/tconbeer/sqlfmt/compare/0.14.1...0.14.2
[0.14.1]: https://github.com/tconbeer/sqlfmt/compare/0.14.0...0.14.1
[0.14.0]: https://github.com/tconbeer/sqlfmt/compare/0.13.0...0.14.0
[0.13.0]: https://github.com/tconbeer/sqlfmt/compare/0.12.0...0.13.0
[0.12.0]: https://github.com/tconbeer/sqlfmt/compare/0.11.1...0.12.0
[0.11.1]: https://github.com/tconbeer/sqlfmt/compare/0.11.0...0.11.1
[0.11.0]: https://github.com/tconbeer/sqlfmt/compare/0.10.1...0.11.0
[0.10.1]: https://github.com/tconbeer/sqlfmt/compare/0.10.0...0.10.1
[0.10.0]: https://github.com/tconbeer/sqlfmt/compare/0.9.0...0.10.0
[0.9.0]: https://github.com/tconbeer/sqlfmt/compare/0.8.0...0.9.0
[0.8.0]: https://github.com/tconbeer/sqlfmt/compare/0.7.0...0.8.0
[0.7.0]: https://github.com/tconbeer/sqlfmt/compare/0.6.0...0.7.0
[0.6.0]: https://github.com/tconbeer/sqlfmt/compare/0.5.1...0.6.0
[0.5.1]: https://github.com/tconbeer/sqlfmt/compare/0.5.0...0.5.1
[0.5.0]: https://github.com/tconbeer/sqlfmt/compare/0.4.3...0.5.0
[0.4.3]: https://github.com/tconbeer/sqlfmt/compare/0.4.2...0.4.3
[0.4.2]: https://github.com/tconbeer/sqlfmt/compare/0.4.1...0.4.2
[0.4.1]: https://github.com/tconbeer/sqlfmt/compare/0.4.0...0.4.1
[0.4.0]: https://github.com/tconbeer/sqlfmt/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/tconbeer/sqlfmt/compare/0.2.1...0.3.0
[0.2.1]: https://github.com/tconbeer/sqlfmt/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/tconbeer/sqlfmt/compare/0.1.0...0.2.0
