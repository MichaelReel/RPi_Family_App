from marshmallow import Schema, fields, post_load, INCLUDE

from lib.metoffice.domain.models import Geometry, Location, TimeSeries, Properties, Feature, Symbol, Unit, ParameterDetails, WeatherSchemaRoot


class GeometrySchema(Schema):
    coordinates = fields.List(fields.Decimal(), required=True)
    type = fields.Str(required=True)

    @post_load
    def make_geometry(self, data, **kwargs):
        return Geometry(**data)

class LocationSchema(Schema):
    licence = fields.Str(allow_none=True)
    name = fields.Str(allow_none=True)

    @post_load
    def make_location(self, data, **kwargs):
        return Location(**data)

class TimeSeriesSchema(Schema):
    class Meta:
        # This tells Marshmallow to accept any dynamic key without failing
        unknown = INCLUDE

    # Evaluates empty objects/arbitrary data mapping
    @post_load
    def make_timeseries(self, data, **kwargs):
        return TimeSeries(data=data)

class PropertiesSchema(Schema):
    modelRunDate = fields.Str(required=True)
    requestPointDistance = fields.Decimal(required=True)
    timeSeries = fields.List(fields.Nested(TimeSeriesSchema), required=True)
    location = fields.Nested(LocationSchema, allow_none=True)

    @post_load
    def make_properties(self, data, **kwargs):
        return Properties(**data)

class FeatureSchema(Schema):
    geometry = fields.Nested(GeometrySchema, required=True)
    properties = fields.Nested(PropertiesSchema, required=True)
    type = fields.Str(required=True)

    @post_load
    def make_feature(self, data, **kwargs):
        return Feature(**data)

class SymbolSchema(Schema):
    type = fields.Str(allow_none=True)
    value = fields.Str(allow_none=True)

    @post_load
    def make_symbol(self, data, **kwargs):
        return Symbol(**data)

class UnitSchema(Schema):
    label = fields.Str(required=True)
    symbol = fields.Nested(SymbolSchema, allow_none=True)

    @post_load
    def make_unit(self, data, **kwargs):
        return Unit(**data)

class ParameterDetailsSchema(Schema):
    description = fields.Str(allow_none=True)
    type = fields.Str(allow_none=True)
    unit = fields.Nested(UnitSchema, allow_none=True)

    @post_load
    def make_parameter_details(self, data, **kwargs):
        return ParameterDetails(**data)

class WeatherSchemaRootSchema(Schema):
    features = fields.List(fields.Nested(FeatureSchema), required=True)
    # Safely maps the "[any-key]: ParameterDetails" dynamic definition structure
    parameters = fields.List(
        fields.Dict(keys=fields.Str(), values=fields.Nested(ParameterDetailsSchema)), 
        required=True
    )
    type = fields.Str(required=True)

    @post_load
    def make_root(self, data, **kwargs):
        return WeatherSchemaRoot(**data)