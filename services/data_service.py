import pandas as pd
import config
import os

class DataService:
    def __init__(self):
        pass

    def load_excel(self, filepath, limit=None):
        print(f"Loading Excel: {filepath}")
        if limit:
            print(f"Limiting to first {limit} rows.")
            df = pd.read_excel(filepath, nrows=limit)
        else:
            df = pd.read_excel(filepath)
        
        # Normalize column names to lowercase for easier access if needed
        # df.columns = [c.lower() for c in df.columns]
        return df

    def save_excel(self, data, filepath):
        print(f"Saving results to: {filepath}")
        df = pd.DataFrame(data)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        df.to_excel(filepath, index=False)
        print("Save complete.")

    def parse_rt_rw(self, address):
        """
        Extract RT and RW from address string.
        Returns tuple (rt, rw) as strings or None.
        Examples: "Jln. Mawar RT 01 RW 02" -> ("01", "02")
                  "Dusun X RT.005/01" -> ("005", "01")
        """
        import re
        if not isinstance(address, str):
            return None, None
            
        # Common patterns
        # RT 01 RW 02
        # RT.01/RW.02
        # RT01 / RW02
        
        # Normalize
        addr_clean = address.upper().replace('.', ' ').replace('/', ' ')
        
        rt = None
        rw = None
        
        # Find RT
        rt_match = re.search(r'RT\s*(\d+)', addr_clean)
        if rt_match:
            rt = rt_match.group(1)
            
        # Find RW
        rw_match = re.search(r'RW\s*(\d+)', addr_clean)
        if rw_match:
            rw = rw_match.group(1)
            
        return rt, rw
