import bffile
import ome_types as ot
import numpy as np
from copy import deepcopy




def extract_input_meta(img_path):
    metadata={"series_count":None,"ome":None,"core":None}
    with bffile.BioFile(img_path) as bf:
        metadata["series_count"]=bf.series_count()
        metadata["ome"]=bf.ome_metadata
        metadata["core"]=bf.core_metadata()
    return metadata

def remap_planes(planes_block,remap_dic,z_slice=None):
    edited_planes=[]
    for p in planes_block:
        if p.the_c in remap_dic:
            p.the_c=remap_dic[p.the_c]
            edited_planes.append(p)

    if isinstance(z_slice,int):
        for n in range(len(edited_planes)):
            edited_planes[n].the_z=0
            
    return edited_planes

def remap_channels(channels_block):
    edited_channels=[]
    for n,c in enumerate(channels_block):
        c.id=f"Channel:{0}:{n}"
        edited_channels.append(c)
    return edited_channels

def remap_images(images_block):
    edited_images=[]
    for n,im in enumerate(images_block):
        im.id=f"Image:{n}"
        edited_images.append(im)
    return edited_images

def create_series_ome(src_metadata,channels,series_id,z_slice=None):

    # Conform channels
    channels_id=sorted(set(channels))
    remap_ch_id = {old: new for new, old in enumerate(channels_id)}

    # Initialize the ome-metadata for the series
    ome_series=ot.model.OME()
    ome_series.instruments=deepcopy(src_metadata.instruments)
    images_block=[deepcopy(src_metadata.images[series_id])]

    # Edit images block
    ome_series.images=remap_images(images_block)

    # Edit channels block
    channels_block=[ome_series.images[0].pixels.channels[ch] for ch in channels_id ]

    ome_series.images[0].pixels.channels=remap_channels(channels_block)

    # Edit the size_c
    ome_series.images[0].pixels.size_c=len(channels_block)

    # Edit the DimensionOrder
    ome_series.images[0].pixels.dimension_order="XYZCT"

    # Edit planes block
    #  Search channels
    planes_unsorted=[ (plane,plane.the_t,plane.the_c,plane.the_z) 
                 for plane in ome_series.images[0].pixels.planes 
                 if np.isin(plane.the_c,channels_id) 
                 ]
    
    planes_block = [ p[0] for p in sorted(planes_unsorted,key=lambda p: (p[1], p[2], p[3])) ]
    if isinstance(z_slice,int):
        planes_block=[p for p in planes_block if p.the_z==z_slice]
        ome_series.images[0].pixels.size_z=1

    planes_block=remap_planes(planes_block,remap_ch_id,z_slice=z_slice)
    ome_series.images[0].pixels.planes=planes_block

    # Create TiffData block to warranty compatibility with visualizers
    tiff_data=[ot.model.TiffData(first_t=p.the_t,first_c=p.the_c,first_z=p.the_z,ifd=n,plane_count=1) 
           for n,p in enumerate(planes_block)
           ]

    ome_series.images[0].pixels.tiff_data_blocks=tiff_data
    ome_xml=ot.to_xml(ome_series)

    return ome_xml