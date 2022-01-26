# sqlfmt CHANGELOG

All notable changes to this project will be documented in this file.

## [Unreleased]

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

[Unreleased]: https://github.com/tconbeer/sqlfmt/compare/0.4.2...HEAD

[0.4.2]: https://github.com/tconbeer/sqlfmt/compare/0.4.1...0.4.2

[0.4.1]: https://github.com/tconbeer/sqlfmt/compare/0.4.0...0.4.1

[0.4.0]: https://github.com/tconbeer/sqlfmt/compare/0.3.0...0.4.0

[0.3.0]: https://github.com/tconbeer/sqlfmt/compare/0.2.1...0.3.0

[0.2.1]: https://github.com/tconbeer/sqlfmt/compare/0.2.0...0.2.1

[0.2.0]: https://github.com/tconbeer/sqlfmt/compare/0.1.0...0.2.0
