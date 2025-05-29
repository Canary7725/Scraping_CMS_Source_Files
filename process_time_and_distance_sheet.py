from email.utils import parsedate_to_datetime
import json
import re
import urllib.request
import pandas as pd
from datetime import datetime
import urllib

def get_file_metadata(file_url):
    requests=urllib.request.Request(file_url,method='HEAD')
    with urllib.request.urlopen(requests) as response:
        headers=response.info()
        date=parsedate_to_datetime(headers.get("Last-Modified"))
        last_modified=date.strftime("%Y-%m-%d")

        content_disposition=headers.get("Content-Disposition")
        match = re.search(r'filename="?([^"]+)"?', content_disposition)
        filename=match.group(1)
        return filename,last_modified


def provider_time_distance_df(file_path,sheet_name,file_url):
    """
    Load the Provider Time & Distance sheet and transform to long format
    with specialty and specialty_code as separate columns
    """
    
    df_wide = load_wide_format(file_path, sheet_name)
    
    df_long = transform_to_long_format(df_wide,file_url)
    
    return df_long

def load_wide_format(file_path, sheet_name=None):
    """
    Load the data in wide format first
    """
    df_full = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    
    header_row_1 = df_full.iloc[1].fillna('')  # Row with specialty names
    header_row_2 = df_full.iloc[2].fillna('')  # Row with specialty codes  
    header_row_3 = df_full.iloc[3].fillna('')  # Row with Time/Distance
    
    new_columns = []
    specialty_info = {} 
    
    base_columns = ['county', 'st', 'county_state', 'ssa_code', 'county_designation']
    
    for i in range(len(df_full.columns)):
        if i < 5:
            new_columns.append(base_columns[i] if i < len(base_columns) else f'col_{i}')
        else:
            specialty_name = str(header_row_1.iloc[i]).strip()
            specialty_code = str(header_row_2.iloc[i]).strip()
            time_distance = str(header_row_3.iloc[i]).strip().lower()            
            if specialty_code and specialty_code != 'nan' and specialty_code != '':
                if specialty_code not in specialty_info:
                    specialty_info[specialty_code] = specialty_name
                
                if 'time' in time_distance:
                    new_columns.append(f'{specialty_code}_time')
                elif 'distance' in time_distance:
                    new_columns.append(f'{specialty_code}_distance')

            else:
                if i > 5 and len(new_columns) > 0:
                    last_col = new_columns[-1]
                    if '_time' in last_col:
                        specialty_code = last_col.replace('_time', '')
                        new_columns.append(f'{specialty_code}_distance')

    df_data = df_full.iloc[4:].copy()
    df_data.columns = new_columns[:len(df_data.columns)]
    df_data = df_data.reset_index(drop=True)
    
    df_data = df_data.dropna(axis=1, how='all')
    
    
    return df_data, specialty_info


def transform_to_long_format(data_tuple,file_url):
    """
    Transform wide format to long format with specialty and specialty_code columns,
    applying schema and setting metadata fields.
    """
    df_wide, specialty_info = data_tuple

    base_cols = ['county', 'st', 'county_state', 'ssa_code', 'county_designation']

    filename,last_modified=get_file_metadata(file_url)

    specialty_cols = [col for col in df_wide.columns if col not in base_cols]

    specialty_codes = set()
    for col in specialty_cols:
        if '_time' in col:
            specialty_codes.add(col.replace('_time', ''))
        elif '_distance' in col:
            specialty_codes.add(col.replace('_distance', ''))
        else:
            specialty_codes.add(col)

    specialty_codes = list(specialty_codes)

    long_data = []
    for _, row in df_wide.iterrows():
        base_data = {col: row[col] for col in base_cols if col in df_wide.columns}

        for spec_code in specialty_codes:
            row_data = base_data.copy()


            specialty_clean = specialty_info.get(spec_code, spec_code)
            specialty_clean = str(specialty_clean).replace('(see notes)', '').strip()
            row_data['specialty'] = specialty_clean

            time_col = f'{spec_code}_time'
            distance_col = f'{spec_code}_distance'
            row_data['time'] = row[time_col] if time_col in df_wide.columns else None
            row_data['distance'] = row[distance_col] if distance_col in df_wide.columns else None
            
            row_data['specialty_cd'] = str(spec_code).zfill(3)

            # Additional metadata
            row_data['file_set'] = filename
            row_data['file_path'] = file_url
            row_data['data_source'] = 'CMS Medicare Advantage Applications'
            row_data['file_date'] = last_modified
            long_data.append(row_data)

    df_long = pd.DataFrame(long_data)
    return df_long

