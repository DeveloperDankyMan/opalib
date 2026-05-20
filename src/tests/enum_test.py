from .. import Enums

Enums.new("HTTPMethod", ["GET", "POST", "PUT", "DELETE"])
print(Enums.HTTPMethod.GET)