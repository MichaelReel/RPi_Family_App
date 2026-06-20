from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Geometry:
    coordinates: list[Decimal]
    type: str

@dataclass
class Location:
    licence: str | None = None
    name: str | None = None

@dataclass
class TimeSeries:
    # Captures an arbitrary layout or structure if it contains nested dynamic keys
    data: dict[str, int | str | Decimal] = field(default_factory=dict)

@dataclass
class Properties:
    modelRunDate: str
    requestPointDistance: Decimal
    timeSeries: list[TimeSeries]
    location: Location | None = None

@dataclass
class Feature:
    geometry: Geometry
    properties: Properties
    type: str

@dataclass
class Symbol:
    type: str | None = None
    value: str | None = None

@dataclass
class Unit:
    label: str
    symbol: Symbol | None = None

@dataclass
class ParameterDetails:
    description: str | None = None
    type: str | None = None
    unit: Unit | None = None

@dataclass
class WeatherSchemaRoot:
    features: list[Feature]
    parameters: list[dict[str, ParameterDetails]]
    type: str