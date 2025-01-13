# rigging_tool
 [WORK IN PROGRESS] A guide-based rigging tool inspired by the MGear framework. Right now it is in early stages.
 [作業中] MGearフレームワークに触発されたガイドベースのリギングツールです。現在、初期段階にあります。

The goal is to eventually have a modular system where guides can be spawned of different types, read and written to a cache. 
+ Read and write to a cache
+ Modularly load different types of guide presets.
+ Position guides and load/unload rig from guides.
+ Eventually build an animation toolkit to work with the generated rig.

+ 目標は、最終的に異なる種類のガイドを生成し、キャッシュに読み書きできるモジュラーシステムを作ることです。

+キャッシュに読み書きする
+異なる種類のガイドプリセットをモジュラーに読み込む
+ガイドを配置し、ガイドからリギングを読み込んだりアンロードしたりする
+最終的に生成されたリギングを使ってアニメーションツールキットを作成する


## Installation

NOTE: Specified to work with python 3. Uses both old and new OpenMaya API.

1. Download the package and zip to your `maya/modules` folder. This specific directory location isn't essential as later we designate package location later.
2. Modify the "MAYA_MODULE_PATH" variable in the `maya/version/Maya.env` file. E.g. `MAYA_MODULE_PATH = path\to\rigging_tool`
3. Finally, load the shelf in your Maya scene and find the shelf folder within the module package directory.

![Animation](https://github.com/user-attachments/assets/fa606a1f-4b7e-47c3-b82a-76cd8a3f0d42)

### Features

![Animation2](https://github.com/user-attachments/assets/2546521d-c214-4a1f-87d4-8b0fc0ab9963)

[WIP]

#### Complete Functionality

##### Namespaces
Right now the main namespace functionality is complete:

+ queries existing namespaces
+ ability to clean the scene up by moving existing namespaces, querying moving objects into different namespaces etc.
+ ability to iterate and generate new namespaces for new rig definitions.

##### Ops + utility libraries

+ Most of the math operations needed to build the rig are complete
+ Most of the utility operations needed to support the tool are complete
  

#### TODO Functionality

##### Guides

- Need to build out more guide type definitions.
- guides need better, cleaner gizmo/gui elements

##### Skeleton
- Skeleton generation needs to be more modular and sophisticated
- code needs refactoring for cleaning up
- check architecture again

##### Rig

- Core rig functionality is still not built.
- Need to finish IK
- Need to start FK
- Need to build out advanced logic: drivers, node graph representation, clean attributes etc.

##### Deformation
- Need to build rig driven deformation logic  (shape key logic)


 
