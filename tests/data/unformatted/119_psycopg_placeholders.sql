SELECT image_data FROM images WHERE id = %s;
SELECT image_data, dividend %% divisor as escaped_mod_operator FROM images WHERE id in (%(one)s, %(two)s, %(three)s, %(f!o^u+r)s);
)))))__SQLFMT_OUTPUT__(((((
select image_data
from images
where id = %s
;
select image_data, dividend %% divisor as escaped_mod_operator
from images
where id in (%(one)s, %(two)s, %(three)s, %(f!o^u+r)s)
;
