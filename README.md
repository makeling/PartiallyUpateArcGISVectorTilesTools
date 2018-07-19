# Read Me

## 1 安装部署指南

本工具安装之前，需要安装 **ArcGIS Pro 2.0或以上版本**。



### 1. 1 添加Python环境变量

为了安装方便，建议在开始安装本工具的依赖包之前，将python的路径加入到Windows环境变量中，随ArcGIS Pro一同自动安装的python 3.5的路径默认如下：*C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3*

如下图设置：

![img](https://github.com/makeling/PartiallyUpateArcGISVectorTilesTools/env.png)



### 1.2 安装pip包

管理员权限启动CMD命令行窗口，安装pip包：

![img](https://github.com/makeling/PartiallyUpateArcGISVectorTilesTools/pip.png)

### 1.3 配置pip环境变量

将pip.exe 所在目录添加至Windows 环境变量，如下图：

![img](https://github.com/makeling/PartiallyUpateArcGISVectorTilesTools/pipEnv.png)

### 1.4 安装第三方类库

管理员权限启动CMD命令行窗口，安装本工具所依赖的第三方类库：**Pysmb，oss2，paramiko**；使用命令 pip install <模块名>，例如下图：

在模块的安装中，机器需要连接Internet，或者事先下载这些包，手动安装。

![img](https://github.com/makeling/PartiallyUpateArcGISVectorTilesTools/pysmb.png)

![img](https://github.com/makeling/PartiallyUpateArcGISVectorTilesTools/oss2.png)

![img](https://github.com/makeling/PartiallyUpateArcGISVectorTilesTools/paramiko.png)

 

​         

## 2 工具简介

高级矢量切片工具箱，主要用于解决矢量切皮的局部更新需求。如果一个大数据量的地图仅更新了很小的一部分，那么无需重建整个地图的矢量切片，而只需要创建感兴趣的区域的部分切片包即可。每个工具均有帮助信息，可以在使用时即时查看，如下简单介绍工具箱的功能：

### 2.1 Create Advanced Vector Tile Package

此工具用于创建原始矢量切片包，区别于ArcGIS Pro中自带的创建矢量切片包工具，此工具生产的矢量切片包中额外包含了切片方案和切片索引，这个生产和打包解包过程自动化完成。 这些随包携带的辅助文件可以确保将来局部更新矢量切片的时候，切片方案一致。并且在这个工具中，可以直接对最大节点数进行控制。

![img](https://github.com/makeling/PartiallyUpateArcGISVectorTilesTools/CreateAdvVTPK.png)

 

### 2.2 Create Part Vector Tile Package

此工具用于按照用户指定的感兴趣区域进行矢量切片的局部更新。 其中原始矢量切片包要求是使用工具Create Advanced Vector Tile Package创建的。工具可以自动解析原始矢量切片包中的辅助文件（切片方案、切片索引），自动用于创建局部矢量切片包。

 

![img](https://github.com/makeling/PartiallyUpateArcGISVectorTilesTools/CreatePartVTPK.png)

### 3. Update Vector Tile Package

此工具用于使用局部切片包更新原始切片包，从而获取最新的矢量切片包。工具中根据矢量切片包中的结构自动实现解包更新打包的功能。

 

![img](https://github.com/makeling/PartiallyUpateArcGISVectorTilesTools/UpdateVTPK.png)

 

### 4. Update Vector Tile Service

此工具用于使用局部切片包更新矢量切片在线服务。工具中根据矢量切片包中的结构自动实现解包更新的功能。

需要用户提供矢量切片服务的URL及Server的账户信息以及Server主机的名称与账户信息即可自动实现更新。并且服务无需重启或任何额外配置，服务无间断自动更新。

![img](https://github.com/makeling/PartiallyUpateArcGISVectorTilesTools/UpdateVTS.png)

 

### 5. Update Vector Tile for OSS

此工具用于使用局部切片包更新阿里云矢量切片在线服务。

![img](https://github.com/makeling/PartiallyUpateArcGISVectorTilesTools/UpdateVTOSS.png)







## 背景

矢量切片是Esri在新版中推出的一项亮点新技术，通过ArcGIS Pro中的工具生成矢量切片包，再通过Portal发布成Vector Tile Service。在前端支持各种应用采用统一的接口进行调用，实现了一体化的平台应用解决方案。矢量切片技术充分利用GPU的渲染能力，以全新方式在设备、浏览器中以矢量的方式展现缓存地图。这项技术解决了传统基于栅格缓存切片展现地图存在的诸多问题：如设备分辨率对地图渲染效果的影响，缓存创建后无法再动态更改样式，生成缓存切片的周期过长，对硬件的需求过大等等。

众所周知，矢量切片包的生成速度相对于传统的栅格切片包具有指数极的性能提升，这也是体现矢量切片优越性的一个重要方面。对于一个常规数据量在100MB-10GB级的数据，全部生成一次矢量切片包的速度在分钟级的级别上。可能正是因为这个原因，截至目前最新版本ArcGIS Pro2.0.2，Esri官方仍未提供局部更新矢量切片包的功能。

虽然矢量切片生成速度很快，但是到了TB级别的大数据来说，生成一次完整的切片包也是需要相当长的时间的，如果仅是更新了局部的小范围数据，那基于更新范围自动化更新矢量切片就是一个非常有实际应用价值的需求。 正是在这样的背景下，我们发起了创建自动化局部更新矢量切片工具的项目。

局部更新矢量切片包中包含了自动化更新矢量切片的工作流，这为后续重新规划Web地图应用的范式提供了广阔空间。举个例子：传统我们针对相对更新频度较低的地图会建议用户创建栅格切片，以提升地图响应性能，改善用户体验。当然新技术背景下，我们可以建议用户采用矢量切片替代这类的需求。对于相对频繁更新数据的服务，由于创建栅格缓存的高代价，传统为了保持数据的动态同步只能采用动态地图服务的方式来满足需求，动态服务在请求级别会在服务器端动态的从数据库中读取数据，动态的在内存中绘制，这不仅增加了数据库和服务器端的压力，而且增加了响应时间，降低了用户体验。过往我们对这类需求除了建议用户增加硬件投入，不断扩容来满足更大并发量之外，似乎对提升单请求的响应效率别无它法，因为这受限于技术本身的限制。有了矢量切片技术，再加上我们的自动化矢量切片更新工具，对于更新频度大于矢量切片更新速度的需求，我们都可以采用矢量切片来替代传统的动态地图服务设计，所有地图都采用矢量切片服务替代，一旦数据更新就自动触发矢量切片更新工作流，实现无缝的切片更新，这个设计既满足了数据更新、地图同步显示，又满足了高性能和高分辨率的地图显示效果，这对于大幅度提升WebGIS用户体验会带来令人惊艳的效果。



 

 

 