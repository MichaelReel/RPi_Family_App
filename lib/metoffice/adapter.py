from datetime import datetime
from decimal import Decimal

from lib.metoffice.models import HumanReadableWeatherReport, DailyForecastPoint
from lib.metoffice.domain.models import WeatherSchemaRoot, TimeSeries

# Weather definition lookup maps
WEATHER_CODE_MAP: dict[int, str] = {
    0: "Clear night", 1: "Sunny day", 2: "Partly cloudy N", 
    3: "Partly cloudy", 5: "Mist", 6: "Fog", 7: "Cloudy", 
    8: "Overcast", 9: "Light rain N", 10: "Light rain", 
    11: "Drizzle", 12: "Light rain", 13: "Heavy rain N", 
    14: "Heavy rain", 15: "Heavy rain", 16: "Sleet N", 
    17: "Sleet", 18: "Sleet", 19: "Hail N", 
    20: "Hail", 21: "Hail", 22: "Light snow N", 
    23: "Light snow", 24: "Light snow", 25: "Heavy snow N", 
    26: "Heavy snow", 27: "Heavy snow", 28: "Thunder N", 
    29: "Thunder", 30: "Thunderstorms"
}

class MetOfficeAdapter:
    
    @staticmethod
    def to_human_readable(root_data: WeatherSchemaRoot) -> HumanReadableWeatherReport:
        """Transforms a strongly typed WeatherSchemaRoot into an application-safe HumanReadableWeatherReport."""
        
        # Pull out the primary feature block safely from the features list index
        feature = root_data.features[0]
        
        # Meta conversions using modern built-in generics
        location_name: str = feature.properties.location.name if feature.properties.location else None
        coordinates: list[Decimal] = feature.geometry.coordinates
        model_run_at: datetime = datetime.fromisoformat(feature.properties.modelRunDate.replace("Z", "+00:00"))
        
        human_days: list[DailyForecastPoint] = []
        entry: TimeSeries
        
        for entry in feature.properties.timeSeries:
            # The inner dictionary holds dynamic, raw weather data
            raw: dict[str, int | str | Decimal] = entry.data
            
            # 1. Parse date parameters using modern union operators
            raw_time: str | None = raw.get("time")
            forecast_date: datetime = datetime.fromisoformat(raw_time.replace("Z", "+00:00")) if raw_time else model_run_at

            # 2. Extract and translate the condition string
            w_code: int | None = raw.get("daySignificantWeatherCode") or raw.get("nightSignificantWeatherCode")
            condition: str = "Unknown"
            if w_code is not None:
                condition = WEATHER_CODE_MAP.get(w_code, f"Unknown Code ({w_code})")

            # 3. Handle numeric visibility metrics natively
            raw_vis: int | float | str | None = raw.get("middayVisibility") or raw.get("midnightVisibility")
            visibility_metres: int | None = int(raw_vis) if raw_vis is not None else None

            # 4. Strictly-typed internal conversion helpers using clean union syntax
            def to_decimal(val: int | str | Decimal | None) -> Decimal | None:
                return Decimal(str(val)) if val is not None else None

            def to_int(val: int | str | Decimal | None) -> int | None:
                return int(val) if val is not None else None

            # 5. Populate the human-readable dataclass target
            day_point: DailyForecastPoint = DailyForecastPoint(
                date=forecast_date,
                max_temperature_c=to_decimal(raw.get("dayMaxScreenTemperature")),
                min_temperature_c=to_decimal(raw.get("nightMinScreenTemperature")),
                max_feels_like_c=to_decimal(raw.get("dayMaxFeelsLikeTemp")),
                rain_probability_pct=to_int(raw.get("dayProbabilityOfRain") or raw.get("nightProbabilityOfRain")),
                snow_probability_pct=to_int(raw.get("dayProbabilityOfSnow") or raw.get("nightProbabilityOfSnow")),
                wind_speed_midday_mph=to_decimal(raw.get("midday10MWindSpeed")),
                wind_direction_midday_deg=to_int(raw.get("midday10MWindDirection")),
                visibility_midday_metres=visibility_metres,
                uv_index_max=to_int(raw.get("maxUvIndex")),
                weather_code=w_code,
                weather_condition=condition
            )
            human_days.append(day_point)
            
        return HumanReadableWeatherReport(
            location_name=location_name,
            coordinates=coordinates,
            model_run_at=model_run_at,
            forecast_days=human_days
        )
