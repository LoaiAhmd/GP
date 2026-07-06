#!/usr/bin/env python3
import sys
import json

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            
            # Extract standard fields
            ts = data.get("ts", "")
            time_part = ts[11:19] if (ts and len(ts) >= 19) else ts
            level = str(data.get("level", "info")).upper()
            logger = data.get("logger", "")
            msg = data.get("msg", "")

            # Build clean dictionary with ordered key structure
            clean_data = {}
            if time_part:
                clean_data["time"] = time_part
            clean_data["level"] = level
            if logger:
                clean_data["logger"] = logger
            clean_data["msg"] = msg
            
            # Add any other useful metadata
            for k, v in data.items():
                if k not in ("ts", "level", "logger", "msg", "container", "podSpec", "isvc", "diff"):
                    clean_data[k] = v
            
            # Print as pretty JSON
            print(json.dumps(clean_data, indent=2), flush=True)
            
        except Exception:
            # Wrap non-JSON logs in a JSON format
            print(json.dumps({"raw": line}), flush=True)

if __name__ == "__main__":
    main()
