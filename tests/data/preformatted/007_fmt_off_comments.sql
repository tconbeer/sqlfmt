--fmt: off

--nospace
--      too many spaces
--
--              
-- very                     very                    long                                        comment
                --
                    --  oddly indented!
            /* multi
line */
/* multi
multi
                    line */
select 1--nospace
union all           --lots  of          space
select 2 /* c */  /* d */     /*e*/
-- 673: blank lines between standalone comments must survive fmt: off

-- like this one

-- and this one, after two blank lines


-- and the blank line before a query must survive, too

select 3
