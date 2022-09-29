# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
import tabula
import io
from dataiku.customrecipe import *
from dataiku import recipe

# Read recipe inputs
folder_param = get_input_names_for_role('example_forms')[0]
example_forms = dataiku.Folder(folder_param)
full_path = example_forms.get_info()['path']
file_names = example_forms.list_paths_in_partition()

# Read recipe outputs
pre_processed_folder_param = get_output_names_for_role('processed_forms')[0]
pre_processed_forms = dataiku.Folder(pre_processed_folder_param)
pre_processed_forms_info = pre_processed_forms.get_info()

def pre_process_dataframe(df):
    shift_headers = True
    header_row = 0
    while shift_headers:
        df = df.dropna(axis='columns', how = "all")
        df.columns = df.columns.fillna('unnamed')
        df.columns = [str(x) for x in df.columns]
        df.columns = [x.lower().strip() for x in df.columns if type(x) == str]
        try:
            counter = len([i for i, x in enumerate(df.columns, 0) if 'unnamed' in x])
        except:
            counter = 0
        if counter > len(df.columns)/2:
            df.columns = df.iloc[header_row]
            df = df.drop(header_row)
            df.columns = df.columns.fillna('unnamed')
            header_row = header_row + 1
        else:
            shift_headers = False
    return df

def upload_excel(df, file):
    path = pre_processed_forms.get_info()['path']
    file_path = path + "/" + file[:file.find(".")] + ".csv"
    df.to_csv(file_path, sep = "|")
    return None

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
def run(file_names):
    error_param = get_output_names_for_role('error')[0]
    error_folder = dataiku.Folder(error_param)
    for file in file_names:
        with example_forms.get_download_stream(file) as stream:
            if file.endswith('.csv'):
                df = pd.read_csv(io.StringIO(stream.read().decode('UTF-8')))
                result_df = pre_process_dataframe(df)
                upload_excel(result_df,file)
            if file.endswith('.xlsx'):
                df = pd.read_excel(full_path + file, engine = "openpyxl")
                result_df = pre_process_dataframe(df)
                upload_excel(result_df,file)
            if file.endswith('.xls'):
                df = pd.read_excel(full_path + file)
                result_df = pre_process_dataframe(df)
                upload_excel(result_df,file)
            if file.endswith('.pdf'):
                df_list = tabula.read_pdf(full_path + file, pages="all")
                if len(df_list) == 0:
                    path = example_forms.file_path(file)
                    with open(path,"rb") as f:
                        error_folder.upload_stream(file, f)
                for df in df_list:
                    result_df = pre_process_dataframe(df)
                    upload_excel(result_df,file)
    return result_df

run(file_names)