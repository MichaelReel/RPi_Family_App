import json
from pathlib import Path
import pytest
from marshmallow import ValidationError

# Import your classes and schemas from your module
from lib.metoffice.domain.models import WeatherSchemaRoot
from lib.metoffice.domain.schemas import WeatherSchemaRootSchema

# A pytest fixture to find and load your sample JSON file safely
@pytest.fixture
def sample_json_data():
    # Looks for sample.json in the same directory as this test file
    file_path = Path("test/test_data/metoffice_sitespecific_point_daily/domain.json").resolve()
    
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def test_schema_loads_valid_json(sample_json_data):
    """Verifies that valid Met Office JSON passes structural validation."""
    schema = WeatherSchemaRootSchema()
    
    # Acts as the main parsing test: raises ValidationError if schema rules fail
    result = schema.load(sample_json_data)
    
    # Asserts the data successfully converted into your root Python dataclass
    assert isinstance(result, WeatherSchemaRoot)
    assert result.type is not None
    assert len(result.features) > 0


def test_extracted_dataclass_values(sample_json_data):
    """Verifies specific deep attributes parse correctly after deserialisation."""
    schema = WeatherSchemaRootSchema()
    weather_obj = schema.load(sample_json_data)
    
    # Test feature geometric structures
    first_feature = weather_obj.features[0]
    assert isinstance(first_feature.geometry.coordinates, list)
    assert isinstance(first_feature.properties.modelRunDate, str)
    
    # Test the dynamic dictionary structure in parameters
    if weather_obj.parameters:
        first_param_dict = weather_obj.parameters[0]
        # Get the first key name dynamically (e.g., 'temperature', 'windSpeed')
        dynamic_key = list(first_param_dict.keys())[0]
        details = first_param_dict[dynamic_key]
        
        assert details.unit is not None
        assert isinstance(details.unit.label, str)


def test_schema_rejects_missing_required_fields():
    """Ensures the schema correctly raises errors on corrupted payloads."""
    schema = WeatherSchemaRootSchema()
    
    # Intentionally missing the required 'features' array
    corrupted_payload = {
        "type": "FeatureCollection",
        "parameters": []
    }
    
    with pytest.raises(ValidationError) as exc_info:
        schema.load(corrupted_payload)
        
    # Validates that Marshmallow explicitly complained about the missing array
    assert "features" in exc_info.value.messages
