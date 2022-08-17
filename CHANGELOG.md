# sqlfmt CHANGELOG

All notable changes to this project will be documented in this file.

## [Unreleased]

### Breaking API Changes
-   The `files` argument of `api.run` is now a `Collection[pathlib.Path]` that represents an exact collection of files to be formatted, instead of a list of paths to search for files. Use `api.get_matching_paths(paths, mode)` to return the set of exact paths expected by `api.run`

### Features
-   sqlfmt will now display a progress bar for long runs ([#231](https://github.com/tconbeer/sqlfmt/pull/231)). You can disable this with the `--no-progressbar` option
-   `api.run` now accepts an optional `callback` argument, which must be a `Callable[[Awaitable[SqlFormatResult]], None]`. Unless the `--single-process` option is used, the callback is executed after each file is formatted.
-   sqlfmt can now be called as a python module, with `python -m sqlfmt`

### Formatting Changes + Bug Fixes
-   adds more granularity to operator precedence and will merge lines more aggressively that start with high-precedence operators ([#200](https://github.com/tconbeer/sqlfmt/issues/200))
-   improves the formatting of `between ... and ...`, especially in situations where the source includes a line break ([#207](https://github.com/tconbeer/sqlfmt/issues/207))
-   fixes a bug that caused unnecessary copying of the cache when using multiprocessing. Large projects should see dramatically faster (near-instant) runs once the cache is warm
-   fixes a bug that could cause lines with long jinja tags to be one character over the line length limit, and could result in unstable formatting ([#237](https://github.com/tconbeer/sqlfmt/issues/237) - thank you [@nfcampos](https://github.com/nfcampos)!)
-   fixes a bug that formatted array literals like they were indexing operations ([#235](https://github.com/tconbeer/sqlfmt/issues/235) - thank you [@nfcampos](https://github.com/nfcampos)!)

## [0.10.1] - 2022-08-05

### Features

-   sqlfmt now supports the psycopg placeholders `%s` and `%(name)s` ([#198](https://github.com/tconbeer/sqlfmt/issues/198) - thank you [@snorkysnark](https://github.com/snorkysnark)!)

### Formatting Changes + Bug Fixes

-   sqlfmt now standardizes whitespace inside word tokens ([#201](https://github.com/tconbeer/sqlfmt/issues/201))
-   `using` is now treated as a word operator. It gets a space before its brackets and merging with surrounding lines is now much improved ([#218](https://github.com/tconbeer/sqlfmt/issues/218) - thank you [@nfcampos](https://github.com/nfcampos)!)
-   `within group` and `filter` are now treated like `over`, and the formatting of those aggregate clauses is improved ([#205](https://github.com/tconbeer/sqlfmt/issues/205))

## [0.10.0] - 2022-08-02

### Features

-   sqlfmt now supports ClickHouse. When run with the `--dialect clickhouse` option, sqlfmt will not lowercase names that could be case-sensitive in ClickHouse, like function names, aliases, etc. ([#193](https://github.com/tconbeer/sqlfmt/issues/193) - thank you [@Shlomixg](https://github.com/Shlomixg)!)

### Formatting Changes + Bug Fixes

-   formatting for chained boolean operators with complex expressions is now significantly improved ([#189](https://github.com/tconbeer/sqlfmt/issues/189) - thank you [@Rainymood](https://github.com/Rainymood)!)
-   formatting for array indexing is now significantly improved ([#209](https://github.com/tconbeer/sqlfmt/issues/209)) and sqlfmt no longer inserts spaces between the `offset()` function and its brackets
-   set operators (like `union`) are now formatted differently. They must be on their own line, and will not cause subsequent blocks to be indented ([#188](https://github.com/tconbeer/sqlfmt/issues/188) - thank you [@Rainymood](https://github.com/Rainymood)!)
-   `select * except (...)` syntax is now explicitly supported, and formatting is improved. Support added for BigQuery and DuckDB star options: `except`, `exclude`, `replace`
-   sqlfmt no longer inserts spaces between nested or repeated brackets, like `(())` or `()[]`
-   a bug causing unstable formatting with long/multiline jinja tags has been fixed ([#175](https://github.com/tconbeer/sqlfmt/issues/175))

## [0.9.0] - 2022-06-02

### Features

-   jinjafmt is now able to format jinja that contains functions and variables that are reserved python words (e.g., return, except, from) ([#177](https://github.com/tconbeer/sqlfmt/issues/177), [#155](https://github.com/tconbeer/sqlfmt/issues/155)), and `~`, the jinja string concatenation operator ([#182](https://github.com/tconbeer/sqlfmt/issues/182))
-   adds a new command-line option to reset the sqlfmt cache ([#184](https://github.com/tconbeer/sqlfmt/issues/184))

### Fixes

-   fixes issue where jinjafmt would insert a trailing comma into multiline macro definitions, causing dbt compiling errors ([#156](https://github.com/tconbeer/sqlfmt/issues/156))
-   fixes issue causing unstable formatting of multiline jinja tags when black is unable to parse the tag ([#176](https://github.com/tconbeer/sqlfmt/issues/176))
-   fixes issue for developers where pre-commit hooks would not install

### Primer

-   sqlfmt_primer now runs against forked (formatted) repos to make changes easier to detect

## [0.8.0] - 2022-05-04

### Formatting Changes

-   sqlfmt is now more conservative about preserving whitespace around jinja expressions when we remove newlines ([#162](https://github.com/tconbeer/sqlfmt/issues/162), [#165](https://github.com/tconbeer/sqlfmt/issues/165) - thank you [@rcaddell](https://github.com/rcaddell) and [@rjay98](https://github.com/rjay98)!)
-   jinja blocks are now dedented before line merging, instead of after. This results in small changes to formatted output in some cases where jinja blocks are used
-   fixes an issue where jinja else and elif statements could cause unstable formatting. May impact whitespace for the tokens following `{% else %}` and `{% elif %}` statements

## [0.7.0] - 2022-04-24

### Breaking Changes

-   api.run now accepts `files` as a `List[pathlib.Path]` instead of a `List[str]`

### Features

-   any command line option can now be set in a `pyproject.toml` file. See `README` for more information ([#90](https://github.com/tconbeer/sqlfmt/issues/90))
-   sqlfmt now accepts an `--exclude` option to specify a glob of files to exclude from formatting ([#131](https://github.com/tconbeer/sqlfmt/issues/131))

## [0.6.0] - 2022-03-21

### Formatting Fixes

-   adds support for snapshot blocks, so the contents of those blocks are now properly formatted ([#137](https://github.com/tconbeer/sqlfmt/issues/137))
-   fixes issue causing unstable formatting of multiline jinja tags when black is not installed ([#138](https://github.com/tconbeer/sqlfmt/issues/138))
-   fixes formatting of semicolons and semicolon-delimited queries ([#132](https://github.com/tconbeer/sqlfmt/issues/132))

## [0.5.1] - 2022-02-08

### Fixes

-   adds support for numbered field references (e.g., `$1`) and snowflake stages (`@my_stage`) as identifiers
-   do not split lines before the `between` operator's `and` keyword ([#124](https://github.com/tconbeer/sqlfmt/issues/124) - thank you [@WestComputing](https://github.com/WestComputing)!)

## [0.5.0] - 2022-02-02

### Formatting changes

-   formats the contents of jinja tags (the code between the curlies) using _black_, the Python formatter. If _black_ is not already installed, you can use this feature by re-installing sqlfmt with the jinjafmt extra (`pipx install sqlfmt[jinjafmt]`). If _black_ is installed, but you do not want to use this feature, you can disable it with the command-line option `--no-jinjafmt`
-   no longer inserts spaces around colons ([#103](https://github.com/tconbeer/sqlfmt/issues/103) - thank you [@noel](https://github.com/noel)!)

### Fixes

-   adds "cross join" to list of supported join types. No longer merges the "cross" keyword with the previous statement ([#110](https://github.com/tconbeer/sqlfmt/issues/110) - thank you [@rdeese](https://github.com/rdeese)!)
-   adds support for every valid operator in postgresql, even the weird ones, like `@>`, `||/`, `?-|` ([#105](https://github.com/tconbeer/sqlfmt/issues/105))

## [0.4.3] - 2022-01-31

### Fixes

-   removes an unnecessary dependency on black that broke installation ([#98](https://github.com/tconbeer/sqlfmt/issues/98) - thank you [@ljhopkins2](https://github.com/ljhopkins2)!)

## [0.4.2] - 2022-01-26

### Features

-   adds an option, `--single-process`, to force single-processing, even when formatting many files

### Under the Hood

-   when formatting multiple files, uses multiprocessing for ~3x faster throughput

## [0.4.1] - 2022-01-20

### Formatting changes

-   preserves leading and trailing blank lines when merging lines with content
-   no longer prints whitespace on blank lines

## [0.4.0] - 2022-01-20

### Formatting changes

-   adds special support for jinja, with new formatting rules for jinja statements, expressions, and blocks
-   safely standardizes whitespace around jinja statements and expressions
-   merges lines within and across jinja blocks while balancing start/end statements
-   jinja block tags can no longr be indented farther than any of their contents

### Features

-   developers can now easily profile sqlfmt performance (after installing the sqlfmt_primer extra) with `make profiling`

### Fixes

-   no longer fails with a parsing error if "end" is used as a name in the query

### Under the Hood

-   refactors lexing using typical callable architecture for more flexibility
-   adds new token types for jinja statements and blocks
-   refactors calculation of node and line depth to include jinja blocks
-   adds some caching to line properties for performance enhancements

## [0.3.0] - 2021-12-16

### Formatting changes

-   refactors comment parsing for improved formatting of comments and merging around comments
-   standardizes comments and splits long comments onto multiple lines if necessary
-   improves splitting and merging of lines with operators (like "+", "as", "on", etc.)
-   improves formatting of queries that use leading commas
-   improves merging of statements with chained brackets ("( something ) + ( something_else )" )

### Features

-   adds a simple cache and skips formatting files that have not changed since last successful run
-   improves the welcome message displayed when running sqlfmt with no arguments

### Fixes

-   supports all postgres and bigquery string literals and quoted identifiers, including triple quotes, escaped quotes, dollar-delimited, etc.
-   no longer fails with a parsing error when encountering a semicolon
-   properly delineates between "\*" as "all fields" and as the multiplication operator

## [0.2.1] - 2021-12-04

### Performance

-   refactors line splitting algorithm and creating a line from nodes; provides 3x speedup of sqlfmt (now formats roughly 100 files/sec)

### Fixes

-   refactored lexer for better parsing of tokens on multiple lines

## [0.2.0] - 2021-11-16

### Features

-   can format text through stdin by passing `-` as the files argument
-   supports `--quiet` option
-   supports `-- fmt: off` and `-- fmt: on` comments in sql files
-   supports more select keywords, like `window` and `qualify`
-   supports back-ticks for quoting relation names
-   supports MySQL-style comments (`# comment`)
-   adds a new cli tool, sqlfmt_primer, to run sqlfmt against known OSS projects to gauge changes

### Fixes

-   fixes parsing of jinja tags (use lazy regex so we don't match multiple tags at once)
-   fixes issue with whitespace around jinja tags
-   fixes capitalization of word operators (on, and, etc.)
-   fixes parsing error caused by comments without leading spaces

## [0.1.0] - 2021-11-08

### Features

-   initial release
-   discovers .sql and .sql.jinja files
-   formats the files it discovers
-   supports --check and --diff options
-   supports --no-color

[Unreleased]: https://github.com/tconbeer/sqlfmt/compare/0.10.1...HEAD

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
