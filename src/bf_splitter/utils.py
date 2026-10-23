import numpy as np
from tifffile import tiffcomment
from loguru import logger
import tracemalloc
import time


def find_home_plane(lazy_array,ref_channel,ref_frame):
    channel_slice=slice(ref_channel,ref_channel+1)
    frame_slice=slice(ref_frame,ref_frame+1)
    aux_arr=np.array(lazy_array[frame_slice,channel_slice,:,:,:])
    result=np.sum(aux_arr,axis=(3,4),keepdims=True)
    result=np.abs(result)
    result=np.floor( result ).astype("int32").squeeze()
    z_home_index= int(np.argwhere(result)[0][0])
    return z_home_index

def append_omexml(file_path,ome_xml):
    tiffcomment(file_path,"")
    tiffcomment(file_path, ome_xml.encode("utf-8"))

def tasks_summary(succeded,failed):
        
    logger.info("SUMMARY:")
    logger.info("SUCCESSFULLY EXTRACTED SERIES:")
    if succeded:
        for element in succeded:
            logger.info(f"SERIES-ID:{element}")
    else:
        logger.info(f"NONE")
        
    logger.info("FAILED EXTRACTED SERIES:")

    if failed:
        for element in failed:
            logger.info(f"SERIES-ID:{element}")
    else:
        logger.info(f"NONE")

def memocron(func):
    def wrapper(*args,**kwargs):
        tracemalloc.start()
        st = time.time()
        result=func(*args,**kwargs)
        print(f'\nRESOURCES USED by {func.__name__} function ')
        print("Memory peak:",((10**(-9))*tracemalloc.get_traced_memory()[1],"GB"))
        rt = time.time() - st
        tracemalloc.stop()
        print("Runtime:",f"{rt // 60:.0f}m {rt % 60:.0f}s")
        return result
    return wrapper