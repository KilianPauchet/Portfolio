with source as (
    select * from {{ source('projet8', 'USER') }}
),

renamed as (
    select
        USER_ID                as user_id,
        PATH_CATEGORY_NAME     as path_category,
        AGE_GROUP              as age_group,
        GENDER                 as gender,
        REGION                 as region,
        YEAR_PATH_STARTED      as year_path_started
    from source
)

select * from renamed