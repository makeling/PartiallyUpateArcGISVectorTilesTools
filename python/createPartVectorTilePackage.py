# -*- coding: utf-8 -*-
# !/usr/bin/python
__author__ = 'mu_xiaoyan'
# Version     : 2.1.0
# Start Time  : 2017-12-07

# Update Time : 2018-09-20
# Change Log :
## Add support for getting known XML

# Update Time : 2018-8-13
# Change Log  :
##  Added new logical to calculate affected bundle extent in each level to avoid vector tile lost
##  New function - calculate_affected_indexes_layer(AOI, index_polygon)
##  Perfectly maintained spatial relationship internal
##  Obsoleted parameter LOD, which now is calculated automatically
##  Automatically removed intermediate data and workspace


import time, zipfile, arcpy
import sys, os, shutil


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
        adv_aux_paras = [index_polygon, tile_scheme, service_type,temp_workspace]
        return adv_aux_paras
    except:
        arcpy.AddError("Original vtpk does not exist.")

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

# Updated at 2018-8-9
# Added new function calculating the exact bundle extent in each level of vector tile
def calculate_affected_indexes_layer(AOI,index_polygon):
    try:
        # in memory variables
        affected_indexes_fc = "in_memory/base_affected_indexes"
        statistics_LOD_tbl = "in_memory/statistics_LOD"
        bundle_polygon_each_level = "in_memory/bundle_index_polygon_each_level"
        timeStamp = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        bundle_index_polygons = 'intermediate_indexes_' + str(timeStamp) + '.shp'
        arcpy.AddMessage(bundle_index_polygons + " Created ! Do not delete it whiling the tool is running.")
        AOI_lyr = arcpy.MakeFeatureLayer_management(AOI, "AOI_lyr_"+ str(timeStamp))
        index_polygon_lyr = arcpy.MakeFeatureLayer_management(index_polygon, "index_lyr_" + str(timeStamp))

        # Finding the max LOD
        arcpy.SelectLayerByLocation_management(index_polygon_lyr, 'INTERSECT', AOI_lyr)
        arcpy.Statistics_analysis(index_polygon_lyr, statistics_LOD_tbl, [["LOD", "MAX"]])
        statistics_LOD = [row[0] for row in arcpy.da.SearchCursor(statistics_LOD_tbl, ['MAX_LOD'])]
        max_lod = statistics_LOD[0]
        arcpy.AddMessage("- Max affected LOD detected "+str(max_lod))
        arcpy.AddMessage("- Partial vector indexes Creating ... ")
        # Finding indexed polygons overlaped AOI
        arcpy.CopyFeatures_management(index_polygon_lyr, affected_indexes_fc)
        arcpy.SelectLayerByAttribute_management(index_polygon_lyr,'CLEAR_SELECTION')
        base_affected_indexes_lyr = arcpy.MakeFeatureLayer_management(affected_indexes_fc, "base_affected_indexes_lyr")
        # Calculating bundle extent in each level
        arcpy.Select_analysis(index_polygon, bundle_index_polygons, '"LOD"<7')
        with arcpy.da.SearchCursor(affected_indexes_fc, ['SHAPE@','LOD']) as cursor:
            for row in cursor:
                if row[1]<=max_lod and row[1]>=7:
                    bundle_lod = row[1]-7
                    arcpy.SelectLayerByAttribute_management(base_affected_indexes_lyr, 'NEW_SELECTION',
                                                            '"LOD" = '+str(bundle_lod))
                    arcpy.SelectLayerByAttribute_management(index_polygon_lyr, 'NEW_SELECTION',
                                                            '"LOD" = ' + str(row[1]))
                    arcpy.SelectLayerByLocation_management(index_polygon_lyr, "WITHIN", base_affected_indexes_lyr, None,
                                                           "SUBSET_SELECTION", "NOT_INVERT")
                    arcpy.CopyFeatures_management(index_polygon_lyr, bundle_polygon_each_level)
                    arcpy.Append_management([bundle_polygon_each_level], bundle_index_polygons, "NO_TEST")
        arcpy.Delete_management("in_memory")
        arcpy.Delete_management(AOI_lyr)
        arcpy.Delete_management(index_polygon_lyr)
        arcpy.Delete_management(base_affected_indexes_lyr)
        arcpy.AddMessage("- Partial vector indexes Generated !")
        return bundle_index_polygons

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
        return ""

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

    # Update 2018-9-20 add boolean parameter to check if the vtpk is advanced
    # Check if the vtpk is advanced
    is_adv_vtpk = arcpy.GetParameter(3)
    arcpy.AddMessage("# Is Advanced Vtpk : {0}.".format(is_adv_vtpk))
    # Specify the index polygon
    index_polygon = arcpy.GetParameter(4)
    arcpy.AddMessage("# Index Polygon path : {0}.".format(index_polygon))

    # Specify name and workspace for new part vtpk
    out_part_vtpk = arcpy.GetParameterAsText(5)
    arcpy.AddMessage("# New part vtpk : {0}.".format(out_part_vtpk))

    execute(in_map, AOI, origin_vtpk, is_adv_vtpk, index_polygon, out_part_vtpk)

# Update 2018-8-10, Calling the new function
# calculating the exact bundle extent in each level of vector tile
def execute(in_map, AOI, origin_vtpk, is_adv_vtpk, index_polygon, out_part_vtpk):

    arcpy.env.workspace = os.path.dirname(out_part_vtpk)
    temp_workspace = None

    # Update 2018-9-20, add support for user defined xml file
    if is_adv_vtpk:
        # analyzing original_vtpk to get the scheme and index polygon feature class
        adv_aux_paras = analysis_original_vtpk(origin_vtpk)
        index_polygon = adv_aux_paras[0]
        tile_scheme = adv_aux_paras[1]
        service_type = adv_aux_paras[2]
        temp_workspace = adv_aux_paras[3]
        arcpy.AddMessage("- Analyzing origin vtpk succesfully! "
                         + "\n - " + index_polygon + "\n - " + tile_scheme + "\n - " + service_type)
    else:
        common_aux_paras = get_tile_scheme_and_index(in_map)
        tile_scheme = common_aux_paras[0]
        service_type = common_aux_paras[1]
        arcpy.AddMessage("- Servcie Type: " + service_type)

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

    # Remove temporary intermediate data
    if os.path.exists(out_part_vtpk) and arcpy.Exists(out_part_vtpk):
        arcpy.Delete_management(os.path.join(arcpy.env.workspace, bundle_index_polygons))
        arcpy.AddMessage("Temp Data deleted - " + bundle_index_polygons)
    if os.path.exists(out_part_vtpk) and temp_workspace is not None:
        shutil.rmtree(temp_workspace)
        arcpy.AddMessage("Temp Data deleted - " + temp_workspace)



if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
