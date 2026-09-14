# Thor 参数化与总成参考

来源：`reference/Thor`，提交 `286b081fe6f056d87c379b884781ef77ff6a0159`，CC BY-SA 4.0。

本轮补查发现，`freecad-src` **确实存在 Assembly.FCStd**，不是只有散件。XML包含6个App::Link，连接AssemblyBase、AssemblyArt1、AssemblyArt2、AssemblyArt3、AssemblyArt4、AssemblyArt56，并有LCS、AttachedTo和AttachmentOffset等装配属性。这修正了仅凭散件目录无法判断总装的局限。

| 源文件 / 总成 | 可确认的对应关系 |
|---|---|
| AssemblyBase / BaseBot、BaseTop、BaseBearingFix、BaseBoxBody | 底座、支承和电控盒壳体 |
| AssemblyArt1 / Art1Body、Art1Bot、Art1Top、Art1GearMotor | 第一转轴及其壳体/传动 |
| AssemblyArt2 / Art2BodyA、Art2BodyB、Art2BodyUnion、Art2SideCover | 第二轴及分体大臂壳体 |
| AssemblyArt3 / Art3Body、Art3Pulley、Art3Tensioner* | 第三轴/肘部传动与张紧 |
| AssemblyArt4 / Art4Body、Art4Bearing*、Art4MotorFix、Art4TransmissionColumn | 前臂roll及轴承/传动柱 |
| AssemblyArt56 / Art56MotorHolderA/B、Art56GearPlate、Art56Interface | 两个腕轴的联合总成，不能按文件数量误认为一个关节 |

FreeCAD实际读取Assembly.FCStd时，6个链接均能定位到本地子总成且返回非空Shape。对Art4和Art56直接查询聚合Shape得到非物理巨量包围盒（约±1e100），因此本轮不把这个聚合结果作为经过验证的实体碰撞模型，也未强行把它转换成我们的Master。原文件未修改。原始读取记录：`analysis/stage2/thor_assembly_check.json`。

抽查Art2BodyA特征树含Spreadsheet、Sketch、Body、Pad、Pocket、Datum与多种特征，适合借鉴“参数入口—草图/基准—实体特征—装配LCS”的组织方式。独立盖板、左右分壳、轴承固定件、走线空间与张紧件便于分工和维护。`step/`、`stl/`提供交换实体和打印网格，不等于所有文件都已形成完整单一实体。

官方装配文档入口：https://thor.angel-lm.com/documentation/assembly/ 。本轮尝试读取HTTPS、HTTP及documentation索引均超时；没有据此猜测网页中的装配步骤。现有源码总成与分件仍可继续参考。

商业项目不直接采用其原始壳体、步进电机、齿轮皮带、尺寸或装配几何。本项目的分段盒壳、轴承座、参数与脚本均新建；CC BY-SA条款保留在参考仓库，发布前按实际使用内容核查。
