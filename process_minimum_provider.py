from email.utils import parsedate_to_datetime
import json
import re
import urllib.request
import pandas as pd
from datetime import datetime
import urllib

def get_minimum_provider_sheet_df(filename,sheet):
    df=pd.read_excel(filename,sheet,header=None)
    spec_code=df.iloc[2].fillna('')

    columns=[]
    columns.append('ssa_code')
    for i in range(len(df.columns)):
        specialty_code=str(spec_code.iloc[i]).strip()
        if specialty_code and specialty_code != 'nan' and specialty_code != '':
            columns.append(specialty_code)
    skip_indices=[0,1,2,4,5,6,7]
    keep_indices=[i for i in  range(len(list(df.columns))) if i  not in skip_indices]
    df_data=df.iloc[3:,keep_indices].copy()
    df_data.columns=columns[:len(df_data.columns)]
    df_data=df_data.reset_index(drop=True)

    df_data=df_data.dropna(axis=1,how='all')
    df_data=df_data.melt(id_vars='ssa_code',var_name='specialty_cd',value_name='min_provider_count')
    return df_data

def get_max_time_and_distance(time_distance_df,filename,sheet):
    minimum_provider_df=get_minimum_provider_sheet_df(filename,sheet)
    columns=['ssa_code','specialty_cd','min_provider_count','time','distance']
    df=minimum_provider_df.merge(time_distance_df, on=['ssa_code','specialty_cd'], how='inner')
    result_df=df[columns]
    result_df.rename(columns={
        'specialty_cd':'hsd_specialty_cd',
        'time':'max_time',
        'distance':'max_distance'
    },inplace=True)

    return result_df
