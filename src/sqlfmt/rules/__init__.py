from functools import partial

from sqlfmt import actions
from sqlfmt.rule import Rule
from sqlfmt.rules.clone import CLONE as CLONE
from sqlfmt.rules.common import (
    ALTER_DROP_FUNCTION,
    ALTER_WAREHOUSE,
    CREATE_CLONABLE,
    CREATE_FUNCTION,
    CREATE_WAREHOUSE,
    group,
)
from sqlfmt.rules.core import CORE as CORE
from sqlfmt.rules.function import FUNCTION as FUNCTION
from sqlfmt.rules.grant import GRANT as GRANT
from sqlfmt.rules.jinja import JINJA as JINJA  # noqa
from sqlfmt.rules.warehouse import WAREHOUSE as WAREHOUSE
from sqlfmt.token import TokenType

MAIN = [
    *CORE,
    Rule(
        name="statement_start",
        priority=1000,
        pattern=group(r"case") + group(r"\W", r"$"),
        action=partial(
            actions.add_node_to_buffer, token_type=TokenType.STATEMENT_START
        ),
    ),
    Rule(
        name="statement_end",
        priority=1010,
        pattern=group(r"end") + group(r"\W", r"$"),
        action=partial(
            actions.safe_add_node_to_buffer,
            token_type=TokenType.STATEMENT_END,
            fallback_token_type=TokenType.NAME,
        ),
    ),
    Rule(
        name="word_operator",
        priority=1100,
        pattern=group(
            r"all",
            r"any",
            r"as",
            r"(not\s+)?between",
            r"cube",
            r"(not\s+)?exists",
            r"filter",
            r"grouping sets",
            r"(not\s+)?in",
            r"is(\s+not)?(\s+distinct\s+from)?",
            r"isnull",
            r"(not\s+)?i?like(\s+any)?",
            r"over",
            r"(un)?pivot",
            r"notnull",
            r"(not\s+)?regexp",
            r"(not\s+)?rlike",
            r"rollup",
            r"some",
            r"(not\s+)?similar\s+to",
            r"tablesample",
            r"within\s+group",
        )
        + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.WORD_OPERATOR),
    ),
    Rule(
        name="star_replace_exclude",
        priority=1101,
        pattern=group(
            r"exclude",
            r"replace",
        )
        + group(r"\s+\("),
        action=partial(
            actions.add_node_to_buffer,
            token_type=TokenType.WORD_OPERATOR,
        ),
    ),
    Rule(
        # a join's using word operator must be followed
        # by parens; otherwise, it's probably a
        # delete's USING, which is an unterminated
        # keyword
        name="join_using",
        priority=1110,
        pattern=group(r"using") + group(r"\s*\("),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.WORD_OPERATOR),
    ),
    Rule(
        name="on",
        priority=1120,
        pattern=group(r"on") + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.ON),
    ),
    Rule(
        name="boolean_operator",
        priority=1200,
        pattern=group(
            r"and",
            r"or",
            r"not",
        )
        + group(r"\W", r"$"),
        action=partial(
            actions.add_node_to_buffer,
            token_type=TokenType.BOOLEAN_OPERATOR,
        ),
    ),
    Rule(
        name="unterm_keyword",
        priority=1300,
        pattern=group(
            r"with(\s+recursive)?",
            (
                r"select(\s+(as\s+struct|as\s+value))?"
                r"(\s+(all|top\s+\d+|distinct))?"
                # select into is ddl that needs additional handling
                r"(?!\s+into)"
            ),
            r"delete\s+from",
            r"from",
            (
                r"(natural\s+)?"
                r"((inner|cross|((left|right|full)(\s+outer)?))\s+)?join"
            ),
            # this is the USING following DELETE, not the join operator
            # (see above)
            r"using",
            r"lateral\s+view(\s+outer)?",
            r"where",
            r"group\s+by",
            r"cluster\s+by",
            r"distribute\s+by",
            r"sort\s+by",
            r"having",
            r"qualify",
            r"window",
            r"order\s+by",
            r"limit",
            r"fetch\s+(first|next)",
            r"for\s+(update|no\s+key\s+update|share|key\s+share)",
            r"when",
            r"then",
            r"else",
            r"partition\s+by",
            r"rows\s+between",
            r"values",
            # in pg, RETURNING can be the last clause of
            # a DELETE statement
            r"returning",
        )
        + group(r"\W", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD),
    ),
    Rule(
        # BQ arrays use an offset(n) function for
        # indexing that we do not want to match. This
        # should only match the offset in limit ... offset,
        # which must be followed by a space
        name="offset_keyword",
        priority=1310,
        pattern=group(r"offset") + group(r"\s+", r"$"),
        action=partial(actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD),
    ),
    Rule(
        name="set_operator",
        priority=1320,
        pattern=group(
            r"(union|intersect|except|minus)(\s+all|distinct)?",
        )
        + group(r"\W", r"$"),
        action=actions.handle_set_operator,
    ),
    Rule(
        name="explain",
        priority=2000,
        pattern=group(r"explain(\s+(analyze|verbose|using\s+(tabular|json|text)))?")
        + group(r"\W", r"$"),
        action=partial(
            actions.handle_nonreserved_keyword,
            action=partial(
                actions.add_node_to_buffer, token_type=TokenType.UNTERM_KEYWORD
            ),
        ),
    ),
    Rule(
        name="grant",
        priority=2010,
        pattern=group(r"grant", r"revoke") + group(r"\W", r"$"),
        action=partial(
            actions.handle_nonreserved_keyword,
            action=partial(actions.lex_ruleset, new_ruleset=GRANT),
        ),
    ),
    Rule(
        name="create_clone",
        priority=2015,
        pattern=group(CREATE_CLONABLE + r"\s+.+?\s+clone") + group(r"\W", r"$"),
        action=partial(
            actions.handle_nonreserved_keyword,
            action=partial(
                actions.lex_ruleset,
                new_ruleset=CLONE,
            ),
        ),
    ),
    Rule(
        name="create_function",
        priority=2020,
        pattern=group(CREATE_FUNCTION, ALTER_DROP_FUNCTION) + group(r"\W", r"$"),
        action=partial(
            actions.handle_nonreserved_keyword,
            action=partial(
                actions.lex_ruleset,
                new_ruleset=FUNCTION,
            ),
        ),
    ),
    Rule(
        name="create_warehouse",
        priority=2030,
        pattern=group(
            CREATE_WAREHOUSE,
            ALTER_WAREHOUSE,
        )
        + group(r"\W", r"$"),
        action=partial(
            actions.handle_nonreserved_keyword,
            action=partial(
                actions.lex_ruleset,
                new_ruleset=WAREHOUSE,
            ),
        ),
    ),
    Rule(
        name="unsupported_ddl",
        priority=2999,
        pattern=group(
            r"alter",
            r"attach\s+rls\s+policy",
            r"cache\s+table",
            r"clear\s+cache",
            r"cluster",
            r"comment",
            r"copy",
            r"create",
            r"deallocate",
            r"declare",
            r"describe",
            r"desc\s+datashare",
            r"desc\s+identity\s+provider",
            r"delete",
            r"detach\s+rls\s+policy",
            r"discard",
            r"do",
            r"drop",
            r"execute",
            r"export",
            r"fetch",
            r"get",
            r"handler",
            r"import\s+foreign\s+schema",
            r"import\s+table",
            # snowflake: "insert into" or "insert overwrite into"
            # snowflake: has insert() function
            # spark: "insert overwrite" without the trailing "into"
            # redshift/pg: "insert into" only
            # bigquery: bare "insert" is okay
            r"insert(\s+overwrite)?(\s+into)?",
            r"list",
            r"lock",
            r"merge",
            r"move",
            # prepare transaction statements are simple enough
            # so we'll allow them
            r"prepare(?!\s+transaction)",
            r"put",
            r"reassign\s+owned",
            r"remove",
            r"rename\s+table",
            r"repair",
            r"security\s+label",
            r"select\s+into",
            r"truncate",
            r"unload",
            r"update",
            r"validate",
        )
        + r"(?!\()"
        + group(r"\W", r"$"),
        action=partial(
            actions.handle_nonreserved_keyword,
            action=partial(actions.add_node_to_buffer, token_type=TokenType.FMT_OFF),
        ),
    ),
]
