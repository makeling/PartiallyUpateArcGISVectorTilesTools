# -*- coding: utf-8 -*-
# !/usr/bin/python
__author__ = 'mu_xiaoyan'
# Version     : 2.0.0
# Start Time  : 2017-12-07
# Update Time : 2018-8-10
# Change Log  :
##      Added new logical to calculate affected bundle extent in each level to avoid vector tile lost.
##      New function - calculate_affected_indexes_layer(AOI,index_polygon)

import arcpy
import os
import shutil
import time
import zipfile
import sys


# uncompress the .zip file to folder
def unzip(newPartZipPath):
    try:
        file_zip = zipfile.ZipFile(newPartZipPath, 'r')
        for file in file_zip.namelist():
            # print "unziping..."
            extractFolder = os.path.splitext(newPartZipPath)[0]
            file_zip.extract(file, extractFolder)
        file_zip.close()
        os.remove(newPartZipPath)
        #arcpy.AddMessage("unzip succeed!")
        return extractFolder
    except:
        arcpy.AddError("unzip failed, please provde a validates path")
        return ""

# Analyzing Original vtpk file to get the tiling scheme and index polygon and also get the service type
def analysis_original_vtpk(origin_vtpk_path):

    origin_workspace = os.path.dirname(origin_vtpk_path)
    origin_vtpk_name = os.path.basename(origin_vtpk_path)
    # Create temp workspace
    timeStamp = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    temp_workspace = os.path.join(origin_workspace, str(timeStamp))
    os.mkdir(temp_workspace)
    try:
        # copy original vtpk
        bak_original_vtpk = shutil.copy(origin_vtpk_path, temp_workspace)
        unzip(bak_original_vtpk)
        # Locate vtpk aux files
        tile_scheme_name = "customizedScheme.xml"
        index_polygon_name = "originMasterIndex.shp"
        vtpk_extract_dir = origin_vtpk_name.split(".")[0]
        arcpy.AddMessage(vtpk_extract_dir)
        aux_files_path = temp_workspace+ r"\\"+ vtpk_extract_dir+ r"\AdvVtpkAuxFiles"
        index_polygon = os.path.join(aux_files_path, index_polygon_name)
        tile_scheme = os.path.join(aux_files_path, tile_scheme_name)
        # get the service type
        if os.path.exists(tile_scheme):
            service_type = "EXISTING"
        else:
            tile_scheme = ""
            service_type = "ONLINE"
        aux_paras = [index_polygon, tile_scheme, service_type,temp_workspace]
        return aux_paras
    except:
        arcpy.AddError("Original vtpk does not exist.")

# Updated at 2018-8-9
# Added new function calculating the exact bundle extent in each level of vector tile
def calculate_affected_indexes_layer(AOI,index_polygon):
    # Finding indexed polygons overlaped AOI
    affected_indexes_fc = "in_memory/base_affected_indexes"
    AOI_lyr = arcpy.MakeFeatureLayer_management(AOI, "AOI_lyr")
    index_polygon_lyr = arcpy.MakeFeatureLayer_management(index_polygon, "index_polygon_lyr")
    index_polygon_lyr.visible = False
    AOI_lyr.visible = False
    arcpy.SelectLayerByLocation_management(index_polygon_lyr, 'INTERSECT', AOI_lyr)
    arcpy.Statistics_analysis(index_polygon_lyr, "in_memory/statistics_LOD", [["LOD", "MAX"]])
    statistics_LOD = [row[0] for row in arcpy.da.SearchCursor("in_memory/statistics_LOD", ['MAX_LOD'])]
    max_lod = statistics_LOD[0]
    arcpy.AddMessage("- Max affected LOD detected "+str(max_lod))
    arcpy.CopyFeatures_management(index_polygon_lyr, affected_indexes_fc)
    arcpy.SelectLayerByAttribute_management(index_polygon_lyr,'CLEAR_SELECTION')
    base_affected_indexes_lyr = arcpy.MakeFeatureLayer_management(affected_indexes_fc, "base_affected_indexes_lyr")

    # Calculating bundle extent in each level
    timeStamp = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    bundle_index_polygons = 'partial_index_polygons_'+str(timeStamp)+'.shp'
    arcpy.Select_analysis(index_polygon, bundle_index_polygons, '"LOD"<7')
    arcpy.AddMessage("- Partial vector indexes Level 1-6 Created !")
    with arcpy.da.SearchCursor(affected_indexes_fc, ['SHAPE@','LOD']) as cursor:
        for row in cursor:
            if row[1]<=max_lod and row[1]>=7:
                bundle_lod = row[1]-7
                arcpy.SelectLayerByAttribute_management(base_affected_indexes_lyr, 'NEW_SELECTION',
                                                        '"LOD" = '+str(bundle_lod))
                arcpy.SelectLayerByAttribute_management(index_polygon_lyr, 'NEW_SELECTION',
                                                        '"LOD" = ' + str(row[1]))
                arcpy.SelectLayerByLocation_management(index_polygon_lyr, "INTERSECT", base_affected_indexes_lyr, None,
                                                       "SUBSET_SELECTION", "NOT_INVERT")
                arcpy.CopyFeatures_management(index_polygon_lyr, "in_memory/bundle_index_polygon_each_level")
                arcpy.Append_management(["in_memory/bundle_index_polygon_each_level"], bundle_index_polygons, "TEST")
                arcpy.AddMessage("- Partial vector indexes Level {0} Created !".format(row[1]))

    return bundle_index_polygons

# Updated at 2018-8-9, Old Function Obsoleted !
# Create Partial VTPK in AOI
# def create_partial_vtpk(workspace, bundle_index_polygons, in_map, out_part_vtpk, service_type, tile_scheme):
#     arcpy.AddMessage(service_type)
#     arcpy.env.workspace = workspace
#     arcpy.AddMessage("Current workspace: {0}".format(arcpy.env.workspace))
#     # Updated at 2018-8-9 , obsoleted the followings
#     # AOI_lyr = arcpy.MakeFeatureLayer_management(AOI, "AOI_lyr")
#     # IndexPolygon_lyr = arcpy.MakeFeatureLayer_management(index_polygon, "IndexPolygon_lyr")
#     # # Finding indexed polygons overlaped AOI
#     # arcpy.SelectLayerByLocation_management(IndexPolygon_lyr, 'intersect', AOI_lyr)
#     # # Finding indexed polygons whose LOD not lower than specified
#     # arcpy.SelectLayerByAttribute_management(IndexPolygon_lyr, 'SUBSET_SELECTION', str(' "LOD" >= ' + str(LOD)))
#     # Update at 2018-7-20
#     # Added timeStamp to the name of the new partial index polygons.
#     # timeStamp = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
#     # partialIndex = 'PartialIndex_'+str(timeStamp)+'.shp'
#     # arcpy.CopyFeatures_management(IndexPolygon_lyr, partialIndex)
#     # IndexPolygon_lyr.visible = False
#     # AOI_lyr.visible = False
#     try:
#         # # Update at 2018-7-20
#         # # Added error reporting when the partial vector tile index has no feature.
#         # flag = arcpy.GetCount_management(partialIndex)
#         # arcpy.AddMessage(partialIndex+" feature counts: "+str(flag[0]))
#         # if int(flag[0]) > 0:
#         #     arcpy.AddMessage('New index layer has been generated.')
#         #     arcpy.CreateVectorTilePackage_management(in_map=in_map,
#         #                                              output_file=out_part_vtpk,
#         #                                              service_type=service_type,
#         #                                              tiling_scheme=tile_scheme,
#         #                                              tile_structure="INDEXED",
#         #                                              index_polygons=partialIndex)
#         # else:
#         #     arcpy.AddError("The LOD value is too large. Try to specify a smaller one.")
#
#
#     # Update at 2018-7-20, optimized Error handling mechanism
#     # Previous Code:
#     ## except Exception as err:
#     ##     arcpy.AddError(err)
#     except arcpy.ExecuteError:
#         severity = arcpy.GetMaxSeverity()
#         if severity == 2:
#             # If the tool returned an error
#             arcpy.AddError("Error occurred \n{0}".format(arcpy.GetMessages(2)))
#         elif severity == 1:
#             # If the tool returned no errors, but returned a warning
#             arcpy.AddWarning("Warning raised \n{0}".format(arcpy.GetMessages(1)))
#         else:
#             # If the tool did not return an error or a warning
#             arcpy.AddMessage(arcpy.GetMessages())
#     # arcpy.Delete_management('NewIndex.shp')
#     return True

def main(argv=None):
    # Input map in the current project
    in_map = arcpy.GetParameterAsText(0)
    arcpy.AddMessage("# Input map : {0}.".format(in_map))

    # Specify the area where the delta new part vtpk need to be created
    AOI = arcpy.GetParameterAsText(1)
    arcpy.AddMessage("# AOI : {0}.".format(AOI))

    # Choose the existing original adv vtpk
    origin_vtpk = arcpy.GetParameterAsText(2)
    arcpy.AddMessage("# Original vtpk : {0}.".format(origin_vtpk))

    # Specify name and workspace for new part vtpk
    out_part_vtpk = arcpy.GetParameterAsText(3)
    arcpy.AddMessage("# New part vtpk : {0}.".format(out_part_vtpk))

    execute(in_map, AOI, origin_vtpk, out_part_vtpk)



# Update 2018-8-10, Calling the new function
# calculating the exact bundle extent in each level of vector tile
def execute(in_map, AOI, origin_vtpk_path, out_part_vtpk):
    arcpy.env.workspace = os.path.dirname(out_part_vtpk)
    # analyzing original_vtpk to get the scheme and index polygon feature class
    aux_paras = analysis_original_vtpk(origin_vtpk_path)
    index_polygon = aux_paras[0]
    tile_scheme = aux_paras[1]
    service_type = aux_paras[2]
    temp_workspace = aux_paras[3]
    arcpy.AddMessage("Analyzing origin vtpk succesfully! "
                     +"\n - "+index_polygon+"\n - "+tile_scheme+"\n - "+service_type)
    # Calculating affected bundle indexes
    bundle_index_polygons = calculate_affected_indexes_layer(AOI, index_polygon)
    arcpy.AddMessage("# Affected exactly index polygons created!  ")
    arcpy.AddMessage("# Starting creating partial vector tiles ...  ")
    arcpy.CreateVectorTilePackage_management(in_map=in_map,
                                             output_file=out_part_vtpk,
                                             service_type=service_type,
                                             tiling_scheme=tile_scheme,
                                             tile_structure="INDEXED",
                                             index_polygons=bundle_index_polygons)
    arcpy.AddMessage("# Partial vector tiles created!  ")
    if os.path.exists(out_part_vtpk):
        shutil.rmtree(temp_workspace)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
