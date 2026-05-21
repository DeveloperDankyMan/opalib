from opalib import enum_extender

Enums = enum_extender.Enums

Enums.new("HTTPMethod", ["GET", "POST", "PUT", "DELETE"])
print(Enums.HTTPMethod.GET)