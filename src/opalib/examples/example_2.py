import opalib.format as format
import opalib.util as util
import opalib.http as http
import opalib.web as web
import opalib.format as F

from .mesh_formats import *

data = []
util.save(data, {
    "params": {
        "gravity": 196.2,
        "jumpPower": 50,
        "walkSpeed": 16,
        "radius": 1,
        "height": 5,
    },
    "mesh": {
        "Name": "Mesh",
        "Visible": True,
        "points": [],
        "c_conns": [],
        "surfaces": [],
        "barriers": [],
        "connections": []
    }
}, F.MeshReq, {})

encoded = util.encode(data)
# print(encoded)
# raw = util.decode(encoded)
# print(raw)

# obj, _ = util.load(raw, 0, F.MeshReq, {})
# print(obj, _)

host = "127.0.0.1"
port = 8080

if __name__ == "__main__":

    def on_success(promise, args):
        success = args.get("Success")
        mesh = args.get("mesh")

    req_promise = http.req({
        "Url": f"http://{host}:{port}/mesh/generate",
        "Method": "POST",
        "Body": encoded
    }).Then(on_success)

    req_promise()