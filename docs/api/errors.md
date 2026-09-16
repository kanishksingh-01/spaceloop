# API Error Formats
Errors return standardized JSON envelopes:
```json
{
  "error": "Geofence Violation",
  "message": "GPS Radar check failed! You are 280m away. Must be within 50m.",
  "distance_meters": 280.0,
  "max_allowed_meters": 50.0
}
```
