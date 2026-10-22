import bfffile 
import argparse
from pathlib import Path
import pandas as pd



def get_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('i',
                        '--input_table',
                        required=True,
                        type=Path,
                        help=''
                        )

    parser.add_argument('-o',
                        '--outdir',
                        required=True,
                        type=Path,
                        help='absolute path of the directory where the ome.tif files will be written'
                        )

    parser.add_argument('-fn',
                        '--output_file_name',
                        required=False,
                        default="verification_report"
                        type=str,
                        help='absolute path of the directory where the ome.tif files will be written'
                        )

    args=parser.parse_args()
    return args

def sum_differences(ima,imb):
    bfa=bfffile.BioFile()
    bfb=bfffile.BioFile()
    lza=bfa.to_dask(series=0,resolution=0)
    lzb=



def main():
    args=get_args()
    input_file=args.input_table
    table=pd.read_csv(input_file)
    
