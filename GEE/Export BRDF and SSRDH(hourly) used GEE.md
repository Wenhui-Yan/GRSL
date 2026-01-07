 

# Export BRDF and SSRDH(hourly) used GEE

For defination of "hourly"：If "TIME"=2018-03-07T18:14:36.922000

​                                                     ssrdh=18:00:00 -19:00:00   ①

​                                          not is ssrdh=17:44:36 -18:44:36   ②

We had tried the second path, there was not much of a gap. Actually,  PAR is an estimated value, which means that multiplying by 0.46 or multiplying by 0.48 and the definition of the hour as to whether it is the first or the second, will always have some small errors exist.

```javascript
//wenhuiyan233@163.com
//2024.5.25
//

var basePath = 'projects/wenhuiyan233/assets/grsl4/';// 基础路径，存放表格，format:year_month_day

// BRDF波段名称
var brdfBands = [
  'BRDF_Albedo_Parameters_Band1_iso', 
  'BRDF_Albedo_Parameters_Band1_vol', 
  'BRDF_Albedo_Parameters_Band1_geo',
  'BRDF_Albedo_Parameters_Band2_iso', 
  'BRDF_Albedo_Parameters_Band2_vol', 
  'BRDF_Albedo_Parameters_Band2_geo'
];

// 定义一个函数来处理和导出数据
var processAndExport = function(date, dateString) {
  var assetId = basePath + dateString; 
  var points = ee.FeatureCollection(assetId);
  // 可视化参数（可根据需要调整）
  //var visParams = {
    //color: 'red', 
    //pointRadius: 2 
  //};

  // 将点添加到地图上（可选）
  // Map.addLayer(points, visParams, 'Points');
  // Map.centerObject(points, 4);

  // MODIS数据集
  var modisCollection = ee.ImageCollection("MODIS/061/MCD43A1")
                          .filterDate(date, date.advance(1, 'day'));
  var modisImage = modisCollection.first();

  // 修改getBRDFWithCoords函数,从特征中提取时间并计算小时
  var getBRDFWithCoords = function(feature) {
    var time = ee.Date(feature.get('TIME'));
    var startHour = time;
    var endHour = time.advance(1, 'hour');
    var ecmwfCollection = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
                            .filterDate(startHour, endHour);
    var ssrdhImage = ecmwfCollection.select('surface_solar_radiation_downwards_hourly').first();

    // 从特征中直接提取经纬度信息
    var lon = feature.get('lon');
    var lat = feature.get('lat');
    var point = ee.Geometry.Point([lon, lat]);
    var brdfValues = modisImage.select(brdfBands).reduceRegion({
      reducer: ee.Reducer.first(),
      geometry: point,
      scale: 500
    });

    var ssrdhValue = ssrdhImage ? ssrdhImage.reduceRegion({
      reducer: ee.Reducer.first(),
      geometry: point,
      scale: 500
    }).get('surface_solar_radiation_downwards_hourly') : null;

    // 合并原特征属性、BRDF值和ssrdh值
    return feature.set(brdfValues)
                  .set('surface_solar_radiation_downwards_hourly', ssrdhValue);
  };

  // 创建新的FeatureCollection来存储带有原属性、BRDF、ssrdh的特征
  var brdfFeatures = points.map(getBRDFWithCoords);

  // 使用dateString作为文件名

  Export.table.toDrive({
    collection: brdfFeatures,
    description: dateString, // 正确使用 dateString 参数
    fileFormat: 'CSV',
    fileNamePrefix: dateString // 正确使用 dateString 参数作为文件名前缀
  });
};

// 为每个日期执行处理和导出，
var startDate = ee.Date('2018-03-07');
var endDate = ee.Date('2018-03-31');
var diff = endDate.difference(startDate, 'day');

for (var i = 0; i <= diff.getInfo(); i++) {
  var currentDate = startDate.advance(i, 'day');
  var formattedDate = currentDate.format('yyyy_MM_dd').getInfo(); // 获取实际字符串值
  processAndExport(currentDate, formattedDate); // 正确传递两个参数
}
```





