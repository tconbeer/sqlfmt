# sqlfmt CHANGELOG

All notable changes to this project will be documented in this file.

## [Unreleased]

-   set operators (like `union`) are now formatted differently. They must be on their own line, and will not cause subsequent blocks to be indented ([#188](https://github.com/tconbeer/sqlfmt/issues/188) - thank you [@Rainymood](https://github.com/Rainymood)!)
-   `select * except(...)` syntax is now explicitly supported, and formatting is improved. Support added for BigQuery and DuckDB star options: `except`, `exclude`, `replace`

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

[Unreleased]: https://github.com/tconbeer/sqlfmt/compare/0.9.0...HEAD

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
