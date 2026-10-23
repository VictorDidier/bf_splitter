# public libraries
import argparse
from pathlib import Path
import bffile
from multiprocessing import Pool
from itertools import repeat,batched
import os
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
# local libraries
from .version import __version__
from .metadata_handler import extract_input_meta,create_series_ome
from .image_writer import write_ometif
from .utils import find_home_plane,append_omexml,tasks_summary,memocron

#CLI
def get_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('-i',
                        '--input_image',
                        required=True,
                        type=Path,
                        help='absolute path to the .nd2 image with multipoints'
                        )

    parser.add_argument('-o',
                        '--outdir',
                        required=True,
                        type=Path,
                        help='absolute path of the directory where the ome.tif files will be written'
                        )


    parser.add_argument('-comp',
                        '--compression_algorithm',
                        required=False,
                        type=str,
                        default=None,
                        choices={"lzw","jpeg2000"},
                        help="select between lzw or jpeg2000"
                        )

    parser.add_argument('-batch',
                        '--batch_size',
                        required=False,
                        type=int,
                        default=None,
                        help="""Integer number that specifies how many series will be
                            extracted in parallel.If not specified the default behaviour is
                            to extract the series sequentially.
                            """
                        )

    parser.add_argument('-con',
                        '--concurrency_model',
                        required=False,
                        type=str,
                        default="processes",
                        choices={"threads","processes"},
                        help="""Integer number that specifies how many series will be
                            extracted in parallel.If not specified the default behaviour is
                            to extract the series sequentially.
                            """
                        )

    parser.add_argument('-v',
                    '--version',
                    action='version',
                    version=f"{__version__}"
                    )


    args=parser.parse_args()
    return args

def process_series(img_path,img_ome,series_id,outdir_bf,outdir_flu,compress):
    bf=bffile.BioFile(img_path)
    bf.open()
    try:
        lazy_array = bf.as_array(series=series_id,resolution=0)
        output_file=f"{img_path.stem}_xy{series_id:02d}.ome.tif"
        bfield_map={ch.name:n for n,ch in enumerate(img_ome.images[series_id].pixels.channels) 
                if ch.name in ("bf","BF")
                }
        
        fluo_map={ch.name:n for n,ch in enumerate(img_ome.images[series_id].pixels.channels) 
              if ch.name not in ("bf","BF") 
                }

        bf_channels=list(bfield_map.values())
        fluo_channels=list(fluo_map.values())

        if bf_channels:
            z_home=find_home_plane(lazy_array,ref_channel=bf_channels[0],ref_frame=0)
            bf_file=write_ometif(lazy_array,bf_channels,outdir_bf,output_file,comp_method=compress,z_slices=z_home)
            ome_xml=create_series_ome(img_ome,bf_channels,series_id,z_slice=z_home)
            append_omexml(bf_file,ome_xml)

        if fluo_channels:
            fluo_file=write_ometif(lazy_array,fluo_channels,outdir_flu,output_file,comp_method=compress,z_slices=None)
            ome_xml=create_series_ome(img_ome,fluo_channels,series_id)
            append_omexml(fluo_file,ome_xml)
        success=True
    except Exception as e:
        print(e)
        bf.close()
        success=False

    bf.close()
    logger.info("SERIES {s} EXTRACTION: {status}".format(s=series_id,
                                                         status="SUCCEDED" if success else "FAILED"
                                                         )
                                                         )
    return (series_id,success)

def as_processes(img_path,img_ome,series_id,outdir_bf,outdir_flu,compress):
    with Pool() as pool:
        func_args=zip(repeat(img_path),
                    repeat(img_ome),
                    series_id,
                    repeat(outdir_bf),
                    repeat(outdir_flu),
                    repeat(compress)
                    )
        result=pool.starmap(process_series,func_args)

    return result




def as_threads(img_path,img_ome,series_id,outdir_bf,outdir_flu,compress):
    _cores = os.cpu_count() or 4
    # Never more workers than tasks
    THREADS_PER_CORE = 8     # ← the factor you tune
    MIN_WORKERS      = 8     # floor, so tiny machines still get reasonable concurrency
    MAX_WORKERS_CAP  = 64    # hard ceiling regardless of core count
    tasks=len(series_id)
    max_workers = min(tasks,max(MIN_WORKERS, min(MAX_WORKERS_CAP, _cores * THREADS_PER_CORE)),)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
            result = list(
                pool.map(
                process_series,
                repeat(img_path),      # not copied — shared reference
                repeat(img_ome),  # not copied — shared reference
                series_id,
                repeat(outdir_bf),
                repeat(outdir_flu),
                repeat(compress),
                        )
                        )
    return result



@memocron
def main():
    #Collect arguments
    args = get_args()
    input_image=args.input_image
    outdir=args.outdir
    batch_size=args.batch_size
    compression=args.compression_algorithm
    concurrency=args.concurrency_model

    outdir_bf=outdir / "BrightField"
    outdir_flu=outdir / "Fluorescence"
    if not outdir_bf.exists():
        outdir_bf.mkdir(parents=True,exist_ok=True)

    if not outdir_flu.exists():
        outdir_flu.mkdir(parents=True,exist_ok=True)

    metadata=extract_input_meta(input_image)
    no_of_series=metadata["series_count"]
    logger.info(f"COMMENCING EXTRACTION OF SERIES FROM: {input_image}")
    logger.info(f"NO. OF SERIES TO EXTRACT: {no_of_series}")
    if batch_size:
        logger.info(f"EXTRACTION METHOD: PARALLEL WITH BATCH-SIZE-{batch_size}")
    else:
        logger.info("EXTRACTION METHOD: SEQUENTIAL")

    process_counter=0
    status=[]
    if batch_size:
        series_batches=[list(element) for element in batched(range(no_of_series),batch_size)]
        for current_batch in series_batches:
            process_counter+=len(current_batch)
            logger.info(f"EXTRACTING SERIES(ID): {current_batch}")
            split_args=[input_image,metadata["ome"],current_batch,outdir_bf,outdir_flu,compression]

            if concurrency=="threads":
                result=as_threads(*split_args)
            elif concurrency=="processes":
                result=as_processes(*split_args)
            
            status.extend(result)#result=(series_id,success= True or False)
            """
            with Pool() as pool:
                
                func_args=zip(repeat(input_image),
                              repeat(metadata["ome"]),
                              s,
                              repeat(outdir_bf),
                              repeat(outdir_flu),
                              repeat(compression)
                              )
                result=pool.starmap(process_series,func_args)
                status.extend(result)#result=(series_id,success= True or False)
                """
                

            logger.info(f"PROCESSED SERIES: {process_counter} out of {no_of_series}")

    else:
        for s in range(no_of_series):
            process_counter+=1
            logger.info(f"EXTRACTING SERIES(ID): {s}")
            result=process_series(input_image,metadata["ome"],s,outdir_bf,outdir_flu,compression)
            logger.info(f"PROCESSED SERIES: {process_counter} out of {no_of_series}")
            status.append(result)#result=(series_id,success= True or False)

    success=[s[0] for s in status if s[1]]
    failed=[s[0] for s in status if not s[1]]
    tasks_summary(success,failed)


if __name__ == '__main__':
    main()
    os._exit(0)

