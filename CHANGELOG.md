# sqlfmt CHANGELOG

All notable changes to this project will be documented in this file.

## [Unreleased]

### Features

- supports --quiet option
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

-   initial release
-   discovers .sql and .sql.jinja files
-   formats the files it discovers
-   supports --check and --diff options
-   supports --no-color

[Unreleased]: https://github.com/tconbeer/sqlfmt/compare/0.1.0...HEAD
