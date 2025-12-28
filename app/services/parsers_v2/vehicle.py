import re
from datetime import datetime
from typing import Optional
from app.models.vehicle_v2 import SentinelVehicle

class VehicleParserV2:
    # 2025.12.21-12.00.00: Vehicle BPC_Laika (DbID: 101) destroyed. Location: X=100.0 Y=200.0 Z=300.0
    # 2025.12.21-12.00.00: Vehicle BPC_Wolfswagen (DbID: 102) spawned. Location: X=100.0 Y=200.0 Z=300.0
    REGEX_VEHICLE = re.compile(r"(?P<timestamp>[\d\.-]+): Vehicle (?P<class>.*?) \(DbID: (?P<id>\d+)\) (?P<action>.*?)\. Location: X=(?P<x>[\d\.-]+) Y=(?P<y>[\d\.-]+) Z=(?P<z>[\d\.-]+)")

    @staticmethod
    def parse(line: str) -> Optional[SentinelVehicle]:
        line = line.strip()
        
        match = VehicleParserV2.REGEX_VEHICLE.search(line)
        if match:
            data = match.groupdict()
            
            return SentinelVehicle(
                timestamp=VehicleParserV2._ts(data["timestamp"]),
                vehicle_id=data["id"],
                vehicle_class=data["class"],
                event_type=data["action"].strip(), # spawned, destroyed, etc.
                location={
                    "x": float(data['x']),
                    "y": float(data['y']),
                    "z": float(data['z'])
                }
            )
            
        return None

    @staticmethod
    def _ts(ts_str: str):
        try:
            return datetime.strptime(ts_str, "%Y.%m.%d-%H.%M.%S")
        except:
            return datetime.utcnow()
