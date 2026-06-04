# Forecasting Algorithms and Base Data Format

This document explains the forecasting principles, algorithms, and base data formats used by PowerTool. It covers three pages: **Day-Ahead Load Forecasting**, **Renewable Forecasting**, and **Annual Load Forecasting**. The first two pages produce short-term MW curves for dispatch-oriented studies, while the annual page produces multi-year energy, peak-load, and typical load-shape estimates for planning studies.

The forecasting module is intentionally lightweight. It is not a replacement for an EMS forecasting subsystem, market-clearing forecast stack, numerical weather prediction system, or enterprise forecasting platform. Its purpose is to provide reproducible and explainable engineering forecasts when the available dataset is modest and the deployment environment must remain simple.

## 1. Overall workflow

The day-ahead workflow is:

1. Load historical CSV data or a bundled sample dataset, then map the columns to a standard schema.
2. Select the target variable: `load_mw` for load, `solar_mw` for solar PV, and `wind_mw` for wind.
3. Fill missing weather drivers. The tool first uses an imported future-weather CSV when available, then same-slot or same-hour historical medians, and finally geography and climate-block baselines. Hourly future weather is linearly interpolated to 1–30 minute forecast points.
4. Build numerical features: time-of-day cycles, weekday and holiday indicators, season, latitude, longitude, altitude, temperature, GHI, wind speed, solar altitude, solar azimuth, plane-of-array irradiance, incidence angle, and PV geometry.
5. Run either the selected single algorithm or the adaptive ensemble.
6. Estimate an empirical P10/P90 uncertainty band from validation or training residuals.
7. Apply renewable-specific physical and operational post-processing, including capacity clipping, solar night-time zeroing, PV weather and temperature correction, and configured special-event adjustments.
8. Report the curve, daily statistics, algorithm metrics, driver text, and optional JSON/CSV exports.

The annual workflow is separate. It reads annual energy, maximum load, GDP, population, and sector structure data; forecasts future annual energy by trend, elasticity, or a composite method; derives annual peak load from load factor, climate, and coincidence-factor assumptions; and generates seasonal 24-hour load shapes.

## 2. Base data format for day-ahead forecasting

### 2.1 Internal row schema

Each historical point is normalized into a dictionary-like row.

| Canonical field | Type | Required | Unit | Applies to | Description |
|---|---:|---:|---:|---|---|
| `timestamp` | datetime | Yes | local standard time | load, solar, wind | Sampling timestamp. The loader does not perform timezone conversion; all rows should use the same local time convention. |
| `load_mw` | numeric | Required for load | MW | load | Historical measured or adjusted system/area load. |
| `solar_mw` | numeric | Required for solar | MW | solar | Historical PV output. Night values may be zero. |
| `wind_mw` | numeric | Required for wind | MW | wind | Historical wind active-power output. |
| `renewable_mw` | numeric | Optional | MW | renewable | If missing and both `solar_mw` and `wind_mw` are available, the loader can compute it as their sum. The forecast itself still uses independent solar or wind targets. |
| `temperature_c` | numeric | Optional | deg C | load, solar, wind | Ambient temperature. Missing values are inferred. |
| `ghi_wm2` | numeric | Optional | W/m2 | solar, auxiliary load feature | Global horizontal irradiance. Night values should be zero. Missing values are inferred. |
| `wind_speed_mps` | numeric | Optional | m/s | wind, auxiliary load feature | Wind speed. Missing values are inferred. |
| `cloud_cover_pct` | numeric | Optional | % | future weather CSV | Cloud cover. If future GHI is absent but cloud cover is present, cloud cover attenuates the inferred GHI. |

Latitude, longitude, altitude, holiday country, PV tilt, and PV azimuth are controlled by `ForecastConfig` or GUI inputs rather than by the historical CSV. Some sample CSV files include `latitude`, `longitude`, or `altitude_m`, but the general CSV loader currently uses the page/configuration geography as the authoritative source.

### 2.2 CSV header mapping

The CSV loader recognizes common English, ISO/RTO-style, competition-style, and Chinese headers. Unknown columns are ignored.

| Canonical field | Recognized header examples |
|---|---|
| `timestamp` | `timestamp`, `time`, `datetime`, `date_time`, `interval_start`, `interval_start_time`, `OPR_DT`, `date`, `日期`, `数据时间`, `时间`, `采样时间` |
| `hour` | `hour`, `HE`, `hour_ending`, `OPR_HR`, `OPR_HOUR`, `小时` |
| `minute_offset` | `Tmstamp`, `minute`, `minutes`, `分钟`, `时刻`, `minute_offset` |
| `interval_index` | `period`, `point`, `point_index`, `interval`, `idx`, `序号`, `点号`, `时段`, `时点`, `96点` |
| `load_mw` | `load_mw`, `demand_mw`, `MW`, `SYS_FCST_ACT_MW`, `SYS_FCT_ACT_MW`, `total_load`, `load`, `负荷`, `统调负荷`, `系统负荷`, `电力负荷`, `实测负荷`, `样本负荷` |
| `solar_mw` | `solar_mw`, `solar`, `pv_mw`, `solar_power_mw`, `光伏`, `光伏功率`, `光伏出力`, `光伏发电` |
| `wind_mw` | `wind_mw`, `wind`, `wind_power_mw`, `Patv`, `active_power`, `风电`, `风电功率`, `风电出力`, `实际功率` |
| `renewable_mw` | `renewable_mw`, `renewables_mw`, `total_renewable_mw`, `renewable`, `ren_mw`, `新能源`, `新能源出力` |
| `temperature_c` | `temperature_c`, `temp_c`, `temperature`, `dry_bulb_c`, `T`, `气温`, `温度`, `环境温度` |
| `ghi_wm2` | `ghi_wm2`, `GHI`, `global_horizontal_irradiance`, `solar_irradiance`, `辐照度`, `总辐照`, `水平辐照` |
| `wind_speed_mps` | `wind_speed_mps`, `wind_speed`, `ws_mps`, `windspeed`, `Wspd`, `wind_mps`, `风速` |
| `cloud_cover_pct` | `cloud_cover_pct`, `cloud_cover`, `cloud`, `cloud_pct`, `clouds`, `total_cloud_cover`, `云量`, `云覆盖率` |

Four time encodings are supported. The first is a complete timestamp such as `2025-06-01 13:15`. The second is `date + hour`; hour-ending values from 1 to 24 are converted to hour-beginning values from 0 to 23. The third is `date + interval index`, where indices 1 to 96 are mapped to 15-minute slots. The fourth is `date + minute offset` or `Day + Tmstamp`, as used by some wind-power competition datasets.

### 2.3 Minimum and recommended data volume

The hard lower bound is 48 historical points. This is only a runnability threshold, not a quality guarantee.

| Forecast target | Minimum | Engineering recommendation | Notes |
|---|---:|---:|---|
| Day-ahead load | 48 points | At least 4–8 weeks at the target resolution | Include weekdays, weekends, holidays, and temperature variation. |
| Day-ahead solar | 48 points | At least 2–8 weeks of output plus irradiance and temperature if available | Include clear, cloudy, and overcast samples. |
| Day-ahead wind | 48 points | Several weeks of wind speed and output | Wind is sensitive to local terrain, turbine status, and curtailment. |
| Annual load | 2 years | 5 or more years of energy, peak load, GDP, and population | Planning results are sensitive to historical trend and sector-growth assumptions. |

### 2.4 Example CSV files

Minimal load example:

```csv
timestamp,load_mw,temperature_c
2025-06-01 00:00,27655.3,23.0
2025-06-01 01:00,27413.8,21.1
2025-06-01 02:00,27196.0,19.2
```

Chinese minute-offset example:

```csv
日期,时刻,统调负荷,气温
2025-06-01,0,67853.8,30.5
2025-06-01,15,67120.4,30.2
2025-06-01,30,66642.1,29.9
```

Renewable example:

```csv
timestamp,solar_mw,wind_mw,temperature_c,ghi_wm2,wind_speed_mps
2025-06-01 00:00,0.0,489.4,22.5,0,6.86
2025-06-01 12:00,6450.0,720.8,31.2,920,5.20
2025-06-01 23:00,0.0,610.0,23.0,0,7.10
```

### 2.5 Future-weather forecast CSV

The day-ahead load and renewable pages now support a separate future-weather forecast CSV. This file does not need target columns such as `load_mw`, `solar_mw`, or `wind_mw`; it only supplies exogenous weather drivers for the forecast date. In the GUI, select a built-in training dataset or import a training CSV, then click **Import Future Weather CSV**, and then run the forecast.

The future-weather CSV needs a time column and at least one of `temperature_c`, `ghi_wm2`, `wind_speed_mps`, or `cloud_cover_pct`. Recommended format:

```csv
timestamp,temperature_c,ghi_wm2,wind_speed_mps,cloud_cover_pct
2025-06-22 00:00,12.3,0,3.7,15
2025-06-22 01:00,12.0,0,3.9,15
2025-06-22 12:00,27.4,730,3.1,38
```

`date + hour`, `date + time`, Chinese `日期 + 时刻`, and 96-point period-index layouts are also supported:

```csv
date,hour,temp_c,ghi,wind_speed,cloud_cover_pct
2025-06-22,1,12.3,0,3.7,15
2025-06-22,13,27.4,730,3.1,38
```

At runtime, weather rows are matched by timestamp. If the forecast output is 15-minute while the weather file is hourly, the tool interpolates between adjacent weather points. Forecast points outside the first/last weather timestamp use the nearest value only when the time gap is no more than 6 hours. Missing weather fields still fall back to historical same-slot statistics and geography/climate baselines. For solar PV, imported GHI is treated as the future weather expectation before PV tilt/azimuth, POA, and temperature-coefficient corrections; if cloud cover is provided without GHI, it attenuates inferred GHI empirically.

The bundled sample file is `data/forecast_samples/future_weather_forecast_sample.csv`.

## 3. Feature engineering for day-ahead forecasts

Each historical and future point is transformed into a numerical feature vector containing:

- Time-cycle terms: first and second harmonic sine/cosine terms of hour-of-day, plus normalized minute slot.
- Week terms: weekday sine/cosine, weekend flag, and holiday flag.
- Season terms: a latitude-aware season value and its square.
- Geographic terms: normalized latitude, longitude, and altitude.
- Weather terms: temperature, quadratic temperature, GHI, and wind speed.
- Solar-geometry terms: solar altitude, solar azimuth, plane-of-array irradiance, incidence-angle cosine, and PV relative power factor.
- PV-geometry terms: panel tilt and panel azimuth sine/cosine.

Missing weather values are filled in this order: imported future-weather CSV when provided, same-slot median, same-hour median, all-sample median, then geography/climate baseline. The geography baseline uses latitude, altitude, climate block, diurnal temperature variation, and solar daylight factor to estimate temperature, GHI, and wind speed.

Built-in holiday calendars cover China (`CN`) and the United States (`US`). Other regions can be added through `data/forecast_holidays.json` or `ForecastConfig.holiday_config_path`.

## 4. Day-ahead algorithms

### 4.1 `adaptive_ensemble`: adaptive ensemble

This is the default algorithm. To keep startup and regression tests lightweight, the default candidate set uses Huber robust regression, ridge regression, hourly analog, slot-wise exponential smoothing, and seasonal naive. scikit-learn tree models remain available as optional algorithms, but they are no longer part of the default candidate set. When enough data are available, the last portion of the historical series is used as a validation block. The validation length is controlled by `validation_min_points` and `validation_fraction`; by default it is about 20% of the history while preserving at least 24 training points.

### 4.2 `sklearn_auto`: scikit-learn automatic engine

This is an optional algorithm. The tool imports scikit-learn lazily only when this algorithm is selected, then attempts gradient boosting and random forest. If both tree models fail, the upper workflow falls back to a safer baseline.

- Gradient boosting: `n_estimators=24`, `max_depth=2`, `learning_rate=0.08`, `random_state=42`.
- Random forest: `n_estimators=12`, `max_depth=6`, `min_samples_leaf=2`, `random_state=42`, `n_jobs=1`.

This mode is suitable for lightweight nonlinear fitting. It can capture nonlinear dependence on temperature, irradiance, and wind speed, but it is less transparent than linear models and remains sensitive to the historical coverage of operating conditions.

Each available algorithm receives a weight based on validation MAE:

```text
w_i = (1 / max(MAE_i, ε)^2) / Σ_j(1 / max(MAE_j, ε)^2)
```

The final forecast is the weighted sum of the candidate forecasts. This is appropriate for engineering screening because the model weight is determined by recent validation performance rather than by a fixed assumption that one model is always best.

### 4.3 `ridge`: ridge regression

Features are scaled by column standard deviation and the model solves:

```text
β = (XᵀX + λI)^+ Xᵀy
ŷ = X_future β
```

The default regularization coefficient is about 0.25. Ridge regression is stable, fast, and useful as a fallback baseline, but it cannot fully represent strong nonlinearities or abrupt operational events.

### 4.4 `huber`: two-pass Huber-weighted ridge regression

The Huber option first fits ridge regression, computes residuals `r`, and estimates a robust residual scale:

```text
s = 1.4826 × median(|r|) + ε
```

It then applies Huber-style weights:

```text
weight = 1,                       |r| ≤ 1.35s
weight = 1.35s / max(|r|, ε),      |r| > 1.35s
```

The final model is weighted ridge regression. This makes the method more tolerant of bad points, short spikes, and partially cleaned operational datasets.

### 4.5 `hourly_analog`: hourly analog method

The analog method searches historical samples from the same time slot or same hour and scores candidates by:

- weather distance in temperature, GHI, and wind speed;
- matching of workday, weekend, or holiday type;
- matching of weekday;
- recency.

The top eight candidates are averaged with weights `1 / (0.08 + score)`. This method is easy to audit and is useful for holiday comparisons or dispatcher experience checks.

### 4.6 `exp_smoothing`: slot-wise exponential smoothing

This method exponentially smooths historical values from the same time slot. It uses `α=0.35` when at least five slot samples exist and `α=0.55` when the sample count is smaller. It is very cheap computationally and emphasizes recent behavior.

### 4.7 `seasonal_naive`: weekly seasonal baseline

The weekly seasonal baseline first uses the value from the same timestamp one week earlier, then the value from the previous day, and finally the same-slot or same-hour historical median. It is not intended to be the most accurate model, but it is a safe baseline when more complex models fail.

## 5. Physical constraints for renewable forecasts

Renewable forecasting supports only two independent resources: `solar`/`光伏` and `wind`/`风电`. The tool does not train a mixed aggregate renewable target because solar and wind have different physical drivers.

### 5.1 Solar PV

After the data-driven model output, the solar workflow applies solar-position and PV-geometry corrections. Solar position is estimated from date, latitude, longitude, nominal timezone, equation of time, solar declination, and hour angle. GHI is modified by a weather factor covering clear, partly cloudy, cloudy, overcast, rain/snow, and haze conditions; cloud cover and a manual irradiance multiplier provide additional control.

Plane-of-array irradiance is decomposed as:

```text
POA = POA_direct + POA_diffuse + POA_ground
```

The direct component is based on DNI and incidence-angle cosine, the diffuse component uses an isotropic approximation, and the ground-reflected component uses GHI, albedo, and panel tilt. Cell temperature is estimated by the NOCT approximation:

```text
T_cell = T_ambient + (NOCT - 20) / 800 × POA
```

The PV relative power factor combines POA relative to clear-sky horizontal reference and temperature derating. Whenever solar altitude is below 0 degrees, the PV forecast, P10, and P90 are forced to zero.

### 5.2 Wind

The wind workflow is data-driven and uses wind speed, time, season, geography, and climate features. The current lightweight implementation does not include a detailed turbine power curve, air-density correction, wake model, or curtailment classifier. Curtailment, forced outage, and maintenance periods should be handled by data cleaning or by special-event configuration.

### 5.3 Capacity limit and special events

If `ForecastConfig.renewable_capacity_mw` is positive, renewable output is clipped to `[0, capacity]`. Special events can be configured in `data/forecast_builtin_config.json`; they support absolute MW adjustments, relative percentage adjustments, start/end times, ramp hours, and lag hours.

## 6. Uncertainty bands and daily statistics

The P10/P90 band is an empirical residual band, not a fully calibrated probabilistic quantile model. The tool uses the configured residual absolute-error quantile, defaulting to `confidence_quantile=0.80`, and imposes a lower bound of roughly 3% of the mean target value. Reported daily statistics include peak, valley, peak-valley difference, mean, load factor or capacity factor, maximum upward ramp, maximum downward ramp, and daily energy or generation.

## 7. Annual load forecasting data format

Annual load forecasting uses a JSON dataset. The built-in sample is `data/annual_load_forecast_sample.json`. The base structure is:

```json
{
  "name": "regional annual load planning sample",
  "source": "data-source note",
  "region": "region name",
  "latitude": 31.85,
  "longitude": 118.92,
  "climate_block": "humid hot-summer/cold-winter climate block",
  "base_year": 2025,
  "history": [
    {
      "year": 2021,
      "energy_gwh": 4680,
      "max_load_mw": 905,
      "gdp_billion": 102,
      "population_million": 1.02,
      "primary_gdp_billion": 3.6,
      "secondary_gdp_billion": 52.7,
      "tertiary_gdp_billion": 45.7
    }
  ],
  "default_inputs": {
    "horizon_years": 10,
    "gdp_growth_pct": 5.2,
    "population_growth_pct": 1.1,
    "primary_growth_pct": 2.0,
    "secondary_growth_pct": 4.6,
    "tertiary_growth_pct": 6.4,
    "coincidence_factor": 0.92,
    "dual_carbon_factor_pct": -0.8,
    "electrification_factor_pct": 1.6
  }
}
```

At least two historical years are required. `energy_gwh` is annual electricity consumption; `max_load_mw` is annual maximum load. GDP and population fields support macro-elasticity estimation. Sector GDP fields improve the interpretation of sector-growth effects; if they are missing, the model can still run but the elasticity explanation is weaker.

## 8. Annual load forecasting algorithms

### 8.1 Trend extrapolation

The trend method blends historical CAGR and a linear trend:

```text
E_trend = 0.55 × E_CAGR + 0.45 × E_linear
```

This reduces overreaction to any single historical year.

### 8.2 Elasticity-coefficient method

The historical electricity/GDP elasticity is estimated from energy CAGR divided by GDP CAGR and clipped to 0.45–1.35. Macro growth is built from GDP, population, and sector-growth assumptions:

```text
sector_growth = 0.08 × primary + 0.58 × secondary + 0.34 × tertiary
macro_growth  = 0.65 × gdp + 0.20 × sector_growth + 0.15 × population
policy_growth = dual_carbon + electrification
energy_growth = max(-2%, elasticity × macro_growth + policy_growth)
```

Future annual energy is then compounded from the base-year energy.

### 8.3 Composite method

The composite method uses:

```text
E = 0.45 × E_trend + 0.55 × E_elasticity
```

It is the default method for the annual planning page. Annual peak load is estimated by combining an energy/load-factor route and a peak-growth route that includes peak CAGR, elasticity growth, climate peak adder, and coincidence-factor adjustment. The P10/P90 uncertainty band widens with forecast horizon.

## 9. Output structure

Each day-ahead forecast point contains:

| Field | Meaning |
|---|---|
| `timestamp` | Forecast timestamp. |
| `value_mw` | Point forecast. |
| `p10_mw`, `p90_mw` | Empirical lower and upper uncertainty bounds. |
| `temperature_c`, `ghi_wm2`, `wind_speed_mps` | Weather drivers used by the point. |
| `drivers` | Human-readable driver description. |
| `poa_wm2`, `solar_altitude_deg`, `solar_azimuth_deg`, `incidence_angle_deg` | Solar geometry and irradiance quantities. |
| `weather_factor`, `pv_power_factor` | Weather and PV relative-power correction factors. |

Annual output includes annual energy, annual maximum load, P10/P90 bands, load factor, and seasonal 24-hour typical load shapes scaled by year.

## 10. Data-quality and applicability checks

Before using a forecast result operationally, check the following:

- Do not mix measured load, weather-normalized load, and forecast load as if they were the same target.
- Identify curtailment, load shedding, demand response, maintenance, and extreme-weather samples; clean them or model them as special events.
- Keep the sampling interval consistent. Mixing 5-minute, 15-minute, and hourly data weakens slot-based models.
- Use consistent units: MW, deg C, W/m2, and m/s.
- Check for daylight-saving-time, timezone, hour-ending, and hour-beginning ambiguity.
- Forecast solar and wind separately before any engineering aggregation.
- For annual studies, cross-check results against customer connection applications, industrial project lists, urban planning, energy planning, and historical peak-load records.

## 11. Improvement recommendations for the lightweight app

The current forecasting module already provides offline samples, flexible CSV headers, multiple algorithms, physical post-processing, and exports. For a lightweight desktop application, the next improvements should prioritize maintainability and input trustworthiness:

1. **Keep the GUI split stable**: `power_tool_gui.py` now acts as the main shell, while common services, dynamics/stability, network parameters and faults, loop closure, forecasting, and COMTRADE waveform pages live in focused mixin modules. Future changes should keep page-specific logic out of the main shell.
2. **Add an import pre-check report**: show detected time column, target column, weather columns, missing rate, sampling interval, duplicate timestamps, and unit risks before running a forecast.
3. **Validate future-weather quality**: future-weather CSV import is now available; the next step is to check coverage, date range, hour-beginning/hour-ending convention, nonzero night GHI, and wind-speed outliers.
4. **Clean release artifacts**: release packages should exclude `__pycache__`, temporary files, and test caches. A packaging script should enforce this automatically.
5. **Close the forecast-review loop**: add an “import actuals, compute MAE/RMSE/MAPE, and store local error history” workflow.
6. **Version and validate configuration**: add schema checks for `forecast_builtin_config.json`, holiday files, special events, and regional defaults.
7. **Improve explainability**: add feature contribution or sensitivity summaries, at least for temperature, GHI, wind speed, holiday flag, and time-of-day effects.
8. **Keep annual forecasting lightweight**: annual planning could accept district-level loads, project lists, and connection capacity, but it should remain a fast planning estimator rather than a full spatial load-forecasting platform.
