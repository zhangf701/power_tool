# Day-Ahead / Annual Load Forecasting

Load forecasting has two tabs: **Day-Ahead Load Forecasting** for dispatch-oriented 24-hour or 96-point curves, and **Annual Load Forecasting** for 5–20 year grid-planning forecasts without spatial load forecasting.

For column names, units, missing-value handling, algorithm formulas, future-weather forecast CSV input, and annual JSON format, see `PowerTool_Forecasting_Algorithms_and_Data_Format.md`.

## Day-Ahead Load Forecasting

The day-ahead load forecasting page estimates a 24-hour load curve and reports next-day peaks, valleys, daily energy, and uncertainty bands. The default resolution is 15 minutes, and users can set any integer interval from 1 to 30 minutes.

### Data

- Bundled offline examples/schema samples: `CAISO_LOAD_SAMPLE`, `ERCOT_LOAD_SAMPLE`, `GEFCOM_LOAD_SAMPLE`, `CSG_LOAD_FORECAST_SCHEMA_SAMPLE`, and `ELECTRICIAN_CUP_LOAD_SCHEMA_SAMPLE`.
- Training CSV import recognizes common headers such as `timestamp` / `time` / `datetime`, `load_mw` / `demand_mw` / `SYS_FCST_ACT_MW` / `total_load`, `temperature_c`, `日期`, `时刻`, `统调负荷`, `负荷`, and `温度`.
- A separate future-weather forecast CSV can be imported without load target columns. It needs a time column and at least one of `temperature_c`, `ghi_wm2`, `wind_speed_mps`, or `cloud_cover_pct`; hourly weather is interpolated to 1–30 minute forecast grids.
- Bundled data are compact demonstration samples. Production studies should use ISO/RTO or utility historical load, weather, holiday, and future-weather forecast data.

### Method

The model builds dispatcher-readable hourly features:

- Hour, weekday, weekend, and holidays.
- Hemisphere-aware season terms.
- Latitude, longitude, altitude, and an automatic climate block.
- Temperature and a quadratic temperature term for cooling/heating sensitivity.
- Missing weather first uses the imported future-weather CSV when available. Uncovered fields then fall back to same-slot/same-hour medians and finally to latitude, longitude, altitude, and climate-block baselines.
- Built-in holidays cover China (CN) and the United States (US); other countries can be added through `data/forecast_holidays.json` or a configured calendar path.

The default engine is the adaptive ensemble, using fast ridge/Huber, hourly-analog, exponential-smoothing, and seasonal-naive components. Optional scikit-learn tree models are imported lazily only when the user selects the corresponding algorithms. The output includes an empirical P10-P90 residual band. High-resolution 1–30 minute outputs use 30-minute anchor interpolation plus light curve smoothing.

## Annual Load Forecasting

The annual load forecasting tab supports planning forecasts for future horizons from 5 to 20 years.

### Inputs

- Historical annual energy and maximum-load data, with a bundled hypothetical `data/annual_load_forecast_sample.json` Jiangnan New District sample.
- Latitude, longitude, and climate block.
- GDP, population, and primary/secondary/tertiary industry growth rates.
- Load coincidence factor.
- Policy adjustments such as dual-carbon targets and re-electrification.

### Methods and outputs

Selectable methods include trend extrapolation, elasticity coefficient, and a composite method. Outputs include annual energy in GWh, maximum load in MW, P10-P90 planning uncertainty bands, load factor, and spring/summer/autumn/winter 24-hour typical load-shape curves. Annual results can be exported as JSON or CSV, including annual indicators, seasonal typical shapes for every year from the base year to the final planning year, and explanatory notes.
