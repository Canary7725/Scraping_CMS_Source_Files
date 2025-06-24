import pandas as pd

def get_minimum_provider_sheet_df(filename, sheet):
    df = pd.read_excel(filename, sheet_name=sheet, header=None)

    spec_code_row = df.iloc[2].fillna('').astype(str).str.strip()

    df_body = df[3:].copy()

    specialty_cols = [
        col for col in df.columns[4:]
        if spec_code_row[col] and spec_code_row[col].lower() != 'nan' and not df_body[col].isna().any()
    ]

    selected_cols = [3] + specialty_cols
    df_data = df_body[selected_cols].copy()

    df_data.columns = ['ssa_code'] + [spec_code_row[col] for col in specialty_cols]
    df_data.reset_index(drop=True, inplace=True)

    df_data = df_data.melt(
        id_vars='ssa_code',
        var_name='specialty_cd',
        value_name='min_provider_count',
    )
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
    })

    return result_df
