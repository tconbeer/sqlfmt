with source as (select * from {{ source('my_application', 'users') }}),
  renamed as (

    select
      --ids
      id,
      nullif(xid,'') as xid,

      --date
      created_on,
      updated_on,

      nullif(email,'') as email,
      
      -- names
      nullif(full_name,'') as full_name,
      nullif(trim(
        case
          when regexp_count(nullif(full_name,''), ' ') = 0
            then nullif(full_name,'')
          when regexp_count(nullif(full_name,''), ' ') = 1
            then split_part(nullif(full_name,''), ' ', 1)
          else regexp_substr(nullif(full_name,''), '.* .* ') -- let's explain what is going on here
        end
      ), 'TEST_USER') as first_name,
      nullif(split_part(nullif(full_name,''), ' ', greatest(2, regexp_count(nullif(full_name,''), ' ')+1)),'') as last_name

    from

      source

    where

      nvl(is_deleted, false) is false
      and id <> 123456 -- a very long comment about why we would exclude this user from this table that we will wrap

  )
select * from renamed
)))))__SQLFMT_OUTPUT__(((((
with
    source as (select * from {{ source('my_application', 'users') }}),
    renamed as (
        
        select
            --ids
            id,
            nullif(xid, '') as xid,
            
            --date
            created_on,
            updated_on,
            
            nullif(email, '') as email,
            
            -- names
            nullif(full_name, '') as full_name,
            nullif(
                trim(
                    case
                        when regexp_count(nullif(full_name, ''), ' ') = 0
                        then nullif(full_name, '')
                        when regexp_count(nullif(full_name, ''), ' ') = 1
                        then split_part(nullif(full_name, ''), ' ', 1)
                        -- let's explain what is going on here
                        else regexp_substr(nullif(full_name, ''), '.* .* ')
                    end
                ),
                'TEST_USER'
            ) as first_name,
            nullif(
                split_part(
                    nullif(full_name, ''),
                    ' ',
                    greatest(2, regexp_count(nullif(full_name, ''), ' ') + 1)
                ),
                ''
            ) as last_name
            
        from source
        where
            
            nvl(is_deleted, false) is false
            -- a very long comment about why we would exclude this user from this table that we will wrap
            and id <> 123456
            
    )
select *
from renamed
