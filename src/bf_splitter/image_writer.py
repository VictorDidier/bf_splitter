import tifffile as tifff
import numpy as np


    
def as_slice(x):
    "Formats a simple integer x into slice object,i.e. (start,stop,step)"
    if isinstance(x, int):
        return slice(x, x + 1)
    if x is None:
        return slice(None)
    return x

def stack_channels(lazy_array, channels, z=None):
    "Always returns 5D (T, len(channels), Z_out, Y, X)."
    z_key = as_slice(z)            # None → full Z; int → single plane
    channel_views = []
    for c in channels:
        v = lazy_array[:, as_slice(c), z_key, :, :]
        channel_views.append(np.array(v))

    return np.concatenate(channel_views, axis=1)



def write_ometif(lazy_array,channels,outdir,file_name,comp_method=None,z_slices=None):
    outfile = outdir / file_name
    with tifff.TiffWriter(outfile, bigtiff=True, ome=False) as tif:
        if z_slices:
            image_array=stack_channels(lazy_array, channels, z=z_slices)
        else:
            image_array=stack_channels(lazy_array,channels)
            
        tif.write(
            data= image_array ,
            dtype=lazy_array.dtype.name,
            photometric="minisblack",
            compression=comp_method,
            compressionargs={} if comp_method in (None,"lzw") else {"level":0},
            metadata={"axes":"TCZYX"}
                    )
    return outfile