# Read Me

## Installation Guild

- Requirement ： ArcGIS Pro 2.0 or later;  Pysmb; oss2; paramiko

- Pip installation required.  more information: https://pip.pypa.io/en/stable/installing/

- Optional:  Add python and pip path to Windows Environments.

- PYSMB, OSS2, PARAMIKO packages required.  we strongly recommend the packages installed via pip.

  `pip install pysmb`

  `pip install oss2`

  `pip install paramiko`

​         

## Introduction

**Partially Update ArcGIS Vector Tiles Toolbox** is based on ArcGIS Pro (version 2.0 or later),  which is desktop end  program that supports creating Vector Tile Package.  This toolbox enables you to update  vector tile package or services partially when the source data is in a pretty large amount.

The toolbox includes 5 tools as below: 

### Create Advanced Vector Tile Package

This tool enables you to create an advanced vector tile package, which contains the Tiling Schema xml file and Tiling Indexed Polygon feature class.  In the way , the schema is packaged with the tiles , so to ensure consistency for updating tiles partially. What's more, you can define Maximum Vertex Count to effect the levels of the tiles. 

### Create Part Vector Tile Package

This tool enables you to generate a partial vector tile package in the specified area of of the whole map extent.  It requires that the Original Vector Tile Package created by the Create Advanced Vector Tile Package tool.  The VTPK generated  by the standard Create Vector Tile Package tool in ArcGIS Pro is not support for this tool.

### Update Vector Tile Package

This tool enables you to update a vector tile package using the partial Vector Tile Package. 

### Update Vector Tile Service

This tool enables you to update a vector tile service using the partial Vector Tile Package. It doesn't require the tile layer service restarted, and the service can runs without interruption during the update . 

The ArcGIS Server Manager account and passwords, and  tile service URL are required.

### Update Vector Tile for OSS

This tool enables you to update a vector tile service on OSS using the partial Vector Tile Package. It doesn't require the tile layer service restarted, and the service can runs without interruption during the update . 

The Service Name, Access Key ID, Access Key Secret, Share Hostname, Bucket Name, Endpoint are required.









 

 

 