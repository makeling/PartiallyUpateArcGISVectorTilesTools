# -*- coding: utf-8 -*-
# !/usr/bin/python
__author__ = 'mu_xiaoyan'
# Version     : 1.1.0
# Start Time  : 2017-12-07
# Update Time : 2018-7-20
# Change Log  :
##      1. Replace arcpy.AddMessage() with arcpy.AddError() so to let the tool throw an exception automatically.
##      2. Optimized Error handling mechanism in Function createVtpkIndexAndPackage()
##      3. Fixed wrong error text during to old Error Handling logic.


import arcpy
import os
import xml.dom.minidom as DOM
import zipfile
import shutil
import sys

# Update 2018-9-21 Drop the old logic
# # Create Vector Tile Package Scheme for Customize Geographic Coordinate System
# # Using 20 fixed Level for the first Version.  It can be better in future version, if necessary.
# def GenerateVtpkTilingScheme(in_map,tileScheme):
#     try:
#         scales = "295829355.454565;147914677.727283;73957338.8636413;36978669.4318207;18489334.7159103;9244667.35795516;4622333.67897758;2311166.83948879;1155583.4197444;577791.709872198;288895.854936099;144447.927468049;72223.9637340247;36111.9818670124;18055.9909335062;9027.99546675309;4513.99773337654;2256.99886668827;1128.49943334414;564.249716672068"
#         arcpy.server.GenerateMapServerCacheTilingScheme(in_map=in_map,
#                                                         tile_origin="-180.0 180.0",
#                                                         output_tiling_scheme=tileScheme,
#                                                         num_of_scales=20,
#                                                         scales=scales,
#                                                         dots_per_inch=96,
#                                                         tile_size="512 x 512")
#         arcpy.AddMessage("tile scheme - ready.")
#         return tileScheme
#     except:
#         arcpy.AddError("input map for tiling scheme invalid.")
#
# # Modify Scheme File to Avoid the tile_Origin Specification Bug of the Pro Tool
# def modifyTilingSchemeFile(tileScheme):
#     try:
#         doc = DOM.parse(tileScheme)
#         tileOriginX = doc.getElementsByTagName('X')
#         tileOriginY = doc.getElementsByTagName('Y')
#         tileOriginX[0].firstChild.data = '-180'
#         tileOriginY[0].firstChild.data = '180'
#         f = open(tileScheme, 'w+')
#         doc.writexml(f)
#         f.close()
#         return True
#     except:
#         arcpy.AddError("tile scheme XML file does not exist.")

# Create Vector Tile Index and then Create Vector Tile Package
def create_vtpk_index_and_package(in_map,service_type,tile_scheme,vertex_count,index_polygon,outVtpk):
    try:
        arcpy.management.CreateVectorTileIndex(in_map=in_map,
                                               out_featureclass=index_polygon,
                                               service_type=service_type,
                                               tiling_scheme=tile_scheme,
                                               vertex_count=vertex_count)
        arcpy.AddMessage("tile index - ready.")
        arcpy.management.CreateVectorTilePackage(in_map=in_map,
                                                 output_file=outVtpk,
                                                 service_type=service_type,
                                                 tiling_scheme=tile_scheme,
                                                 tile_structure="INDEXED",
                                                 min_cached_scale="",
                                                 max_cached_scale="",
                                                 index_polygons=index_polygon,
                                                 summary=None,
                                                 tags=None)
        arcpy.AddMessage("Pro standard tile package - ready!")
        return outVtpk
    # Update at 2018-7-20, optimized Error handling mechanism
    # Previous Code:
    # except:
    #   arcpy.AddError("input map for packaging invalid. Check the coordinate system of the input map.")
    except arcpy.ExecuteError:
        severity = arcpy.GetMaxSeverity()
        if severity == 2:
            # If the tool returned an error
            arcpy.AddError("Error occurred \n{0}".format(arcpy.GetMessages(2)))
        elif severity == 1:
            # If the tool returned no errors, but returned a warning
            arcpy.AddWarning("Warning raised \n{0}".format(arcpy.GetMessages(1)))
        else:
            # If the tool did not return an error or a warning
            arcpy.AddMessage(arcpy.GetMessages())

# Append the tiling scheme and index polygon to the standard vtpk
def add_to_zip(original_zip, newfolder):
    try:
        # print("zip file: " + original_zip)
        folder = os.path.dirname(original_zip)
        prelen = len(folder)
        fp = zipfile.ZipFile(original_zip, mode='a')
        for parent, dirnames, filenames in os.walk(newfolder):
            for filename in filenames:
                pathfile = os.path.join(parent, filename)
                # print("pathfile",pathfile)
                arcname = pathfile[prelen:].strip(os.path.sep)
                # print("arcname",arcname)
                fp.write(pathfile, arcname)
        fp.close()
        return True
    except:
        arcpy.AddError("path or folderName not exist.")

# Clear the scratch data
def delete_zip_folder(delete_path):
    shutil.rmtree(delete_path)

# Updated at 2018-9-21
# Automatically finding xml file and allowing user to choose origin index polygon
def get_tile_scheme_and_index(in_map):
    try:
        arcpy.AddMessage("# Starting finding existing XML file ...")
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        map = aprx.listMaps(in_map)[0]
        # getting xml file
        map_sr = map.defaultCamera.getExtent().spatialReference
        map_sr_name = map_sr.name
        map_sr_wkid = map_sr.factoryCode
        vtpk_xml_name = "VTTS_"+str(map_sr_wkid)+"_"+map_sr_name+".xml"
        local_path = os.path.join(os.path.expanduser("~"), "AppData\Local\ESRI\Geoprocessing")
        vtpk_xml_path = os.path.join(local_path,vtpk_xml_name)
        arcpy.AddMessage("# Bingo! " + vtpk_xml_path + " has been found!")
        tile_scheme = vtpk_xml_path
        # getting service type
        if map_sr_wkid == 3857:
            service_type = "ONLINE"
        else:
            service_type = "EXISTING"
        # building index polygons
        common_aux_paras = [tile_scheme, service_type]
        return common_aux_paras
    except:
        arcpy.AddError("Failed to get tile scheme")


# the main method of this script
def execute(in_map,outVtpk,isOnline,vertex_count):
    vtpkDir = os.path.join(os.path.dirname(outVtpk), "AdvVtpkAuxFiles")
    # arcpy.AddMessage("TempFolder"+vtpkDir)
    if not os.path.exists(vtpkDir):
        os.makedirs(vtpkDir)

    # Updated 2018-9-21
    common_aux_paras = get_tile_scheme_and_index(in_map)
    tile_scheme = common_aux_paras[0]
    arcpy.AddMessage(tile_scheme)
    service_type = common_aux_paras[1]
    shutil.copy(tile_scheme,vtpkDir)
    index_polygon = vtpkDir + "\originMasterIndex.shp"

    # # Update 2018-9-21 Drop the old logic
    # if isOnline:
    #     service_type = "ONLINE"
    #     tileScheme = ""
    #     arcpy.AddMessage("service type:"+service_type)
    # else:
    #     service_type = "EXISTING"
    #     arcpy.AddMessage("service type:"+service_type)
    #     GenerateVtpkTilingScheme(in_map,tileScheme)
    #     arcpy.AddMessage(tileScheme)
    #     modifyTilingSchemeFile(tileScheme)

    originalVTPK = create_vtpk_index_and_package(in_map,service_type,tile_scheme,vertex_count,index_polygon,outVtpk)
    if add_to_zip(originalVTPK, vtpkDir):
        delete_zip_folder(vtpkDir)

    arcpy.AddMessage("advanced vector tile package has been generated.")


def main(argv=None):
    # Input map in current project
    in_map = arcpy.GetParameterAsText(0)
    arcpy.AddMessage("Input map : {0}.".format(in_map))

    # Specify name and workspace for the output vtpk
    outVtpk = arcpy.GetParameterAsText(1)
    arcpy.AddMessage("Output advanced vtpk  : {0}.".format(outVtpk))

    #  Specify service type
    isOnline = arcpy.GetParameter(2)
    arcpy.AddMessage("isOnline:"+str(isOnline))

    # Specify maximum vertex count
    vertex_count = arcpy.GetParameterAsText(3)
    arcpy.AddMessage("Maximum vertex count : {0}.".format(vertex_count))

    execute(in_map,outVtpk,isOnline,vertex_count)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))