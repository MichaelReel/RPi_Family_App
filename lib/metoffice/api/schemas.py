from typing import Any

from marshmallow import INCLUDE, Schema, fields, post_load

from lib.metoffice.api.models import (
    Feature,
    Geometry,
    Location,
    ParameterDetails,
    Properties,
    Symbol,
    TimeSeries,
    Unit,
    WeatherSchemaRoot,
)


class GeometrySchema(Schema):
    coordinates = fields.List(fields.Decimal(), required=True)
    type = fields.Str(required=True)

    @post_load
    def make_geometry(self, data: dict[str, Any], **kwargs: Any) -> Geometry:
        return Geometry(**data)


class LocationSchema(Schema):
    licence = fields.Str(allow_none=True)
    name = fields.Str(allow_none=True)

    @post_load
    def make_location(self, data: dict[str, Any], **kwargs: Any) -> Location:
        return Location(**data)


class TimeSeriesSchema(Schema):
    class Meta:
        # This tells Marshmallow to accept any dynamic key without failing
        unknown = INCLUDE

    # Evaluates empty objects/arbitrary data mapping
    @post_load
    def make_timeseries(self, data: dict[str, Any], **kwargs: Any) -> TimeSeries:
        return TimeSeries(data=data)


class PropertiesSchema(Schema):
    model_run_date = fields.Str(required=True, data_key="modelRunDate")
    request_point_distance = fields.Decimal(required=True, data_key="requestPointDistance")
    time_series = fields.List(fields.Nested(TimeSeriesSchema), required=True, data_key="timeSeries")
    location = fields.Nested(LocationSchema, allow_none=True)

    @post_load
    def make_properties(self, data: dict[str, Any], **kwargs: Any) -> Properties:
        return Properties(**data)


class FeatureSchema(Schema):
    geometry = fields.Nested(GeometrySchema, required=True)
    properties = fields.Nested(PropertiesSchema, required=True)
    type = fields.Str(required=True)

    @post_load
    def make_feature(self, data: dict[str, Any], **kwargs: Any) -> Feature:
        return Feature(**data)


class SymbolSchema(Schema):
    type = fields.Str(allow_none=True)
    value = fields.Str(allow_none=True)

    @post_load
    def make_symbol(self, data: dict[str, Any], **kwargs: Any) -> Symbol:
        return Symbol(**data)


class UnitSchema(Schema):
    label = fields.Str(required=True)
    symbol = fields.Nested(SymbolSchema, allow_none=True)

    @post_load
    def make_unit(self, data: dict[str, Any], **kwargs: Any) -> Unit:
        return Unit(**data)


class ParameterDetailsSchema(Schema):
    description = fields.Str(allow_none=True)
    type = fields.Str(allow_none=True)
    unit = fields.Nested(UnitSchema, allow_none=True)

    @post_load
    def make_parameter_details(
        self, data: dict[str, Any], **kwargs: Any
    ) -> ParameterDetails:
        return ParameterDetails(**data)


class WeatherSchemaRootSchema(Schema):
    features = fields.List(fields.Nested(FeatureSchema), required=True)
    # Safely maps the "[any-key]: ParameterDetails" dynamic definition structure
    parameters = fields.List(
        fields.Dict(keys=fields.Str(), values=fields.Nested(ParameterDetailsSchema)),
        required=True,
    )
    type = fields.Str(required=True)

    @post_load
    def make_root(self, data: dict[str, Any], **kwargs: Any) -> WeatherSchemaRoot:
        return WeatherSchemaRoot(**data)
