from src.bio_clients import _RealBioAdapter, MockBioCultureClient, FinalSparkAdapter, CL1Adapter

import os

os.environ.setdefault("NERVE_WML_BIO_API_KEY", MockBioCultureClient().__str__())

adapter = FinalSparkAdapter()

frame = adapter.roundtrip([0.1, 0.8, 0.75])
print(frame.spikes, frame.latency_ms)