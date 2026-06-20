from datetime import datetime
from decimal import Decimal

from lib.metoffice.models import HumanReadableWeatherReport, DailyForecastPoint
from lib.metoffice.domain.models import WeatherSchemaRoot, TimeSeries

# Weather definition lookup maps
WEATHER_CODE_MAP: dict[int, str] = {
    0: "Clear night", 1: "Sunny day", 2: "Partly cloudy (night)", 
    3: "Partly cloudy (day)", 5: "Mist", 6: "Fog", 7: "Cloudy", 
    8: "Overcast", 9: "Light rain shower (night)", 10: "Light rain shower (day)", 
    11: "Drizzle", 12: "Light rain", 13: "Heavy rain shower (night)", 
    14: "Heavy rain shower (day)", 15: "Heavy rain", 16: "Sleet shower (night)", 
    17: "Sleet shower (day)", 18: "Sleet", 19: "Hail shower (night)", 
    20: "Hail shower (day)", 21: "Hail", 22: "Light snow shower (night)", 
    23: "Light snow shower (day)", 24: "Light snow", 25: "Heavy snow shower (night)", 
    26: "Heavy snow shower (day)", 27: "Heavy snow", 28: "Thunder shower (night)", 
    29: "Thunder shower (day)", 30: "Thunderstorms"
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
                weather_condition=condition
            )
            human_days.append(day_point)
            
        return HumanReadableWeatherReport(
            location_name=location_name,
            coordinates=coordinates,
            model_run_at=model_run_at,
            forecast_days=human_days
        )
