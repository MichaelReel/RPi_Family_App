from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from lib.metoffice.domain.models import WeatherSchemaRoot
from lib.metoffice.models import (
    DailyForecastPoint,
    HourlyForecastPoint,
    HumanReadableWeatherReport,
    ThreeHourlyForecastPoint,
)


def _to_decimal(val: int | str | Decimal | None) -> Decimal | None:
    """Convert a value to Decimal, returning None if the input is None."""
    return Decimal(str(val)) if val is not None else None


def _to_int(val: int | str | Decimal | None) -> int | None:
    """Convert a value to int, returning None if the input is None."""
    return int(val) if val is not None else None


def _to_str(val: int | str | Decimal | None) -> str | None:
    """Convert a value to str, returning None if the input is None."""
    return str(val) if val is not None else None


# Weather definition lookup maps
_WEATHER_CODE_MAP: dict[int, str] = {
    0: "Clear night",
    1: "Sunny day",
    2: "Partly cloudy N",
    3: "Partly cloudy",
    5: "Mist",
    6: "Fog",
    7: "Cloudy",
    8: "Overcast",
    9: "Light rain N",
    10: "Light rain",
    11: "Drizzle",
    12: "Light rain",
    13: "Heavy rain N",
    14: "Heavy rain",
    15: "Heavy rain",
    16: "Sleet N",
    17: "Sleet",
    18: "Sleet",
    19: "Hail N",
    20: "Hail",
    21: "Hail",
    22: "Light snow N",
    23: "Light snow",
    24: "Light snow",
    25: "Heavy snow N",
    26: "Heavy snow",
    27: "Heavy snow",
    28: "Thunder N",
    29: "Thunder",
    30: "Thunderstorms",
}


class MetOfficeAdapter:
    @staticmethod
    def to_human_readable(
        daily_root: WeatherSchemaRoot | None,
        hourly_root: WeatherSchemaRoot | None,
        three_hourly_root: WeatherSchemaRoot | None = None,
    ) -> HumanReadableWeatherReport:
        """Transforms strongly typed schema roots into an application-safe HumanReadableWeatherReport."""

        location_name: str | None = None
        coordinates: list[Decimal] = []
        model_run_at: datetime = datetime.now(ZoneInfo("UTC"))

        if daily_root:
            feature = daily_root.features[0]
            location_name = (
                feature.properties.location.name
                if feature.properties.location
                else None
            )
            coordinates = feature.geometry.coordinates
            model_run_at = datetime.fromisoformat(
                feature.properties.model_run_date.replace("Z", "+00:00")
            )

        days = MetOfficeAdapter._to_daily_report(daily_root)
        hourly = MetOfficeAdapter._to_hourly_report(hourly_root)
        three_hourly = MetOfficeAdapter._to_three_hourly_report(three_hourly_root)

        return HumanReadableWeatherReport(
            location_name=location_name,
            coordinates=coordinates,
            model_run_at=model_run_at,
            forecast_days=days,
            forecast_hourly=hourly,
            forecast_three_hourly=three_hourly,
        )

    @staticmethod
    def _to_daily_report(
        root_data: WeatherSchemaRoot | None,
    ) -> list[DailyForecastPoint]:
        """Convert daily TimeSeries entries to DailyForecastPoint list."""
        if root_data is None:
            return []

        feature = root_data.features[0]
        model_run_at = datetime.fromisoformat(
            feature.properties.model_run_date.replace("Z", "+00:00")
        )
        human_days: list[DailyForecastPoint] = []

        for entry in feature.properties.time_series:
            raw: dict[str, int | str | Decimal] = entry.data

            raw_time: str | None = _to_str(raw.get("time"))
            forecast_date: datetime = (
                datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                if raw_time
                else model_run_at
            )

            w_code: int | None = _to_int(
                raw.get("daySignificantWeatherCode")
                or raw.get("nightSignificantWeatherCode")
            )
            condition: str = "Unknown"
            if w_code is not None:
                condition = _WEATHER_CODE_MAP.get(w_code, f"Unknown Code ({w_code})")

            raw_vis = raw.get("middayVisibility") or raw.get("midnightVisibility")
            visibility_metres: int | None = (
                int(raw_vis) if raw_vis is not None else None
            )

            day_point: DailyForecastPoint = DailyForecastPoint(
                date=forecast_date,
                max_temperature_c=_to_decimal(raw.get("dayMaxScreenTemperature")),
                min_temperature_c=_to_decimal(raw.get("nightMinScreenTemperature")),
                max_feels_like_c=_to_decimal(raw.get("dayMaxFeelsLikeTemp")),
                rain_probability_pct=_to_int(
                    raw.get("dayProbabilityOfRain") or raw.get("nightProbabilityOfRain")
                ),
                snow_probability_pct=_to_int(
                    raw.get("dayProbabilityOfSnow") or raw.get("nightProbabilityOfSnow")
                ),
                wind_speed_midday_mph=_to_decimal(raw.get("midday10MWindSpeed")),
                wind_direction_midday_deg=_to_int(raw.get("midday10MWindDirection")),
                visibility_midday_metres=visibility_metres,
                uv_index_max=_to_int(raw.get("maxUvIndex")),
                weather_code=w_code,
                weather_condition=condition,
            )
            human_days.append(day_point)

        return human_days

    @staticmethod
    def _to_hourly_report(
        root_data: WeatherSchemaRoot | None,
    ) -> list[HourlyForecastPoint]:
        """Convert hourly TimeSeries entries to HourlyForecastPoint list."""
        if root_data is None:
            return []

        feature = root_data.features[0]
        model_run_at = datetime.fromisoformat(
            feature.properties.model_run_date.replace("Z", "+00:00")
        )
        hourly_points: list[HourlyForecastPoint] = []

        for entry in feature.properties.time_series:
            raw: dict[str, int | str | Decimal] = entry.data

            raw_time: str | None = _to_str(raw.get("time"))
            point_time: datetime = (
                datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                if raw_time
                else model_run_at
            )

            point = HourlyForecastPoint(
                time=point_time,
                screen_temperature_c=_to_decimal(raw.get("screenTemperature")),
                min_screen_temperature_c=_to_decimal(raw.get("minScreenAirTemp")),
                max_screen_temperature_c=_to_decimal(raw.get("maxScreenAirTemp")),
                feels_like_temperature_c=_to_decimal(raw.get("feelsLikeTemperature")),
                wind_speed_10m_mph=_to_decimal(raw.get("windSpeed10m")),
                wind_gust_10m_mph=_to_decimal(raw.get("windGustSpeed10m")),
                wind_direction_10m_deg=_to_int(raw.get("windDirectionFrom10m")),
                relative_humidity_pct=_to_decimal(raw.get("screenRelativeHumidity")),
                precipitation_rate_mmh=_to_decimal(raw.get("precipitationRate")),
                total_precip_amount_mm=_to_decimal(raw.get("totalPrecipAmount")),
                prob_of_precipitation_pct=_to_int(raw.get("probOfPrecipitation")),
                uv_index=_to_int(raw.get("uvIndex")),
                significant_weather_code=_to_int(raw.get("significantWeatherCode")),
            )
            hourly_points.append(point)

        return hourly_points

    @staticmethod
    def _to_three_hourly_report(
        root_data: WeatherSchemaRoot | None,
    ) -> list[ThreeHourlyForecastPoint]:
        """Convert 3-hourly TimeSeries entries to ThreeHourlyForecastPoint list."""
        if root_data is None:
            return []

        feature = root_data.features[0]
        model_run_at = datetime.fromisoformat(
            feature.properties.model_run_date.replace("Z", "+00:00")
        )
        three_hourly_points: list[ThreeHourlyForecastPoint] = []

        for entry in feature.properties.time_series:
            raw: dict[str, int | str | Decimal] = entry.data

            raw_time: str | None = _to_str(raw.get("time"))
            point_time: datetime = (
                datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                if raw_time
                else model_run_at
            )

            point = ThreeHourlyForecastPoint(
                time=point_time,
                screen_temperature_c=_to_decimal(raw.get("screenTemperature")),
                min_screen_temperature_c=_to_decimal(raw.get("minScreenAirTemp")),
                max_screen_temperature_c=_to_decimal(raw.get("maxScreenAirTemp")),
                feels_like_temperature_c=_to_decimal(raw.get("feelsLikeTemp")),
                wind_speed_10m_mph=_to_decimal(raw.get("windSpeed10m")),
                wind_gust_10m_mph=_to_decimal(raw.get("windGustSpeed10m")),
                wind_direction_10m_deg=_to_int(raw.get("windDirectionFrom10m")),
                relative_humidity_pct=_to_decimal(raw.get("screenRelativeHumidity")),
                precipitation_rate_mmh=_to_decimal(raw.get("precipitationRate")),
                total_precip_amount_mm=_to_decimal(raw.get("totalPrecipAmount")),
                prob_of_precipitation_pct=_to_int(raw.get("probOfPrecipitation")),
                uv_index=_to_int(raw.get("uvIndex")),
                significant_weather_code=_to_int(raw.get("significantWeatherCode")),
            )
            three_hourly_points.append(point)

        return three_hourly_points
