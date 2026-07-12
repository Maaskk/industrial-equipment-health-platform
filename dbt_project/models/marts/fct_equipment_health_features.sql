-- Point-in-time-safe feature table consumed by scripts/train_model.py.
-- Every value depends only on the current or preceding cycles; no engine-final
-- cycle is used, avoiding train/serving leakage.
with features as (
    select
        engine_id,
        cycle,
        setting_1, setting_2, setting_3,
        sensor_1, sensor_2, sensor_3, sensor_4, sensor_5,
        sensor_6, sensor_7, sensor_8, sensor_9, sensor_10,
        sensor_11, sensor_12, sensor_13, sensor_14, sensor_15,
        sensor_16, sensor_17, sensor_18, sensor_19, sensor_20,
        sensor_21,
        source_file,
        case when source_file like 'train_%' then 'train' else 'test' end as split,
        cast(regexp_extract(source_file, 'FD([0-9]+)', 1) as integer) as subset_id,
        ln(1 + cast(cycle as double)) as cycle_log1p,
        case
            when cycle < 75 then 'early'
            when cycle < 150 then 'middle'
            else 'late'
        end as engine_age_bucket,

        -- rolling mean 5
        avg(sensor_1)  over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_1_rolling_mean_5,
        avg(sensor_2)  over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_2_rolling_mean_5,
        avg(sensor_3)  over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_3_rolling_mean_5,
        avg(sensor_4)  over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_4_rolling_mean_5,
        avg(sensor_7)  over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_7_rolling_mean_5,
        avg(sensor_11) over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_11_rolling_mean_5,
        avg(sensor_12) over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_12_rolling_mean_5,
        avg(sensor_15) over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_15_rolling_mean_5,

        -- rolling std 5
        stddev(sensor_1)  over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_1_rolling_std_5,
        stddev(sensor_2)  over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_2_rolling_std_5,
        stddev(sensor_3)  over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_3_rolling_std_5,
        stddev(sensor_4)  over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_4_rolling_std_5,
        stddev(sensor_7)  over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_7_rolling_std_5,
        stddev(sensor_11) over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_11_rolling_std_5,
        stddev(sensor_12) over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_12_rolling_std_5,
        stddev(sensor_15) over (partition by engine_id order by cycle rows between 4 preceding and current row) as sensor_15_rolling_std_5

    from {{ ref('stg_sensor_readings') }}
)

select * from features
