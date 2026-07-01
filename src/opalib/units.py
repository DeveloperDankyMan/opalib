"""
opalib.units
Unit conversion helpers for length and custom measures.
"""

# Base length conversion factors to meters
LENGTH_TO_METERS = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "km": 1000.0,
    "in": 0.0254,
    "ft": 0.3048,
    "yd": 0.9144,
    "mi": 1609.344
}

def convert_length(value: float, from_unit: str, to_unit: str) -> float:
    """
    Converts a length value from one unit to another.
    
    :param value: The numerical value to convert.
    :param from_unit: The unit to convert from (e.g., 'mi', 'km').
    :param to_unit: The unit to convert to (e.g., 'm', 'ft').
    :return: The converted length value.
    """
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    
    if from_unit not in LENGTH_TO_METERS or to_unit not in LENGTH_TO_METERS:
        raise ValueError(f"Unsupported length unit. Choose from: {list(LENGTH_TO_METERS.keys())}")
        
    # Convert to standard meters, then to target unit
    value_in_meters = value * LENGTH_TO_METERS[from_unit]
    return value_in_meters / LENGTH_TO_METERS[to_unit]


def convert_custom(value: float, from_scale: float, to_scale: float) -> float:
    """
    Generic converter for custom measures using base scales (e.g., ratios, 
    batch conversions, or arbitrary units).
    
    $result = value \times \frac{from\_scale}{to\_scale}$
    
    :param value: The amount of the custom measure you have.
    :param from_scale: The base ratio or unit size of your starting measure.
    :param to_scale: The base ratio or unit size of your target measure.
    :return: The converted custom value.
    """
    if to_scale == 0:
        raise ValueError("The 'to_scale' cannot be zero.")
        
    return value * (from_scale / to_scale)
