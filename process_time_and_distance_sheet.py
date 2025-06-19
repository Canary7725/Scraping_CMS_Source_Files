import pandas as pd
import re
from email.utils import parsedate_to_datetime
import urllib.request


def extract_file_metadata(file_url):
    request = urllib.request.Request(file_url, method='HEAD')
    with urllib.request.urlopen(request) as response:
        headers = response.info()
        last_modified = parsedate_to_datetime(headers.get("Last-Modified")).strftime("%Y-%m-%d")

        content_disposition = headers.get("Content-Disposition", "")
        match = re.search(r'filename="?([^"]+)"?', content_disposition)
        filename = match.group(1) if match else file_url.split('/')[-1].split('?')[0]

    return filename, last_modified


def load_and_transform_provider_time_distance(file_path, sheet_name, file_url):
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    header_1 = df.iloc[1].fillna('').astype(str).str.strip()  # Specialty Name
    header_2 = df.iloc[2].fillna('').astype(str).str.strip()  # Specialty Code
    header_3 = df.iloc[3].fillna('').astype(str).str.strip().str.lower()  # time/distance

    base_columns = ['county', 'st', 'county_state', 'ssa_code', 'county_designation']
    column_map = {}
    specialty_info = {}

    for i in range(df.shape[1]):
        if i < 5:
            column_map[i] = base_columns[i]
        else:
            code = header_2[i]
            label = header_1[i]
            measure = header_3[i]

            if code and code.lower() != 'nan':
                specialty_info[code] = label
                if 'time' in measure:
                    column_map[i] = f'{code}_time'
                elif 'distance' in measure:
                    column_map[i] = f'{code}_distance'
            else:
                if column_map.get(i - 1, '').endswith('_time'):
                    prev_code = column_map[i - 1].replace('_time', '')
                    column_map[i] = f'{prev_code}_distance'

    df_data = df.iloc[4:].copy()
    df_data.columns = [column_map.get(i, f'col_{i}') for i in range(df.shape[1])]
    df_data.dropna(axis=1, how='all', inplace=True)
    df_data.reset_index(drop=True, inplace=True)

    value_vars = [col for col in df_data.columns if col not in base_columns]
    df_long = df_data.melt(id_vars=base_columns, value_vars=value_vars,
                           var_name='specialty_measure', value_name='value')

    df_long[['specialty_cd', 'measure']] = df_long['specialty_measure'].str.extract(r'([A-Za-z0-9]+)_?(time|distance)?')
    df_long['specialty_cd'] = df_long['specialty_cd'].str.zfill(3)

    df_pivot = df_long.pivot_table(
        index=base_columns + ['specialty_cd'],
        columns='measure',
        values='value',
        aggfunc='first'
    ).reset_index()

    df_pivot.columns.name = None
    df_pivot['time'] = df_pivot.get('time')
    df_pivot['distance'] = df_pivot.get('distance')

    df_pivot['specialty'] = df_pivot['specialty_cd'].map(
        lambda cd: str(specialty_info.get(cd, cd)).replace('(see Notes)', '').strip()
    )

    filename, last_modified = extract_file_metadata(file_url)
    df_pivot['file_set'] = filename
    df_pivot['file_path'] = file_url
    df_pivot['file_date'] = last_modified
    df_pivot['data_source'] = 'CMS Medicare Advantage Applications'
    return df_pivot
  
