//create high quality mosaic image

// create geometry for area to export mosaic
// in this example, the Great Barrier Reef (GBR)

var geometry = /* color: #d63000 */ee.Geometry.Polygon(
        [[[145.19870569417498, -16.58091711074189],
          [145.22067835042498, -16.675659156118012],
          [145.62717249104998, -18.258042208381408],
          [146.38522913167498, -19.61930223468266],
          [148.36276819417498, -20.691889389018694],
          [151.29611780354998, -20.68161139621467],
          [151.57077600667498, -19.43292140377713],
          [149.75803186604998, -19.08028585257877],
          [149.51633264729998, -19.391474298962248],
          [148.63742639729998, -19.152949176697433],
          [149.02194788167498, -18.1536786895917],
          [147.40695764729998, -17.6832755377528],
          [147.56076624104998, -16.48612839632201],
          [145.18771936604998, -16.465057923576175]]]);

// create a mask function to use the QA bits and other information
// to mask out clouds and shadows

function mask(img){
  // Bits 3 and 5 are cloud shadow and cloud, respectively.
  var cloudShadowBitMask = (1 << 3);
  var cloudsBitMask = (1 << 5);
  // Get the pixel QA band.
  var qa = img.select('pixel_qa');
  // Both flags should be set to zero, indicating clear conditions.
  var ma = qa.bitwiseAnd(cloudShadowBitMask).eq(0)
                 .and(qa.bitwiseAnd(cloudsBitMask).eq(0));
  ma = ma.focal_min({kernel: ee.Kernel.circle({radius: 1}), iterations: 1});
  img = img.mask(ma);
    img = img.updateMask(img.select([3]).lt(1000));
    img = img.updateMask(img.select([4]).lt(300));
  
    var ndwi_revise = (img.select([2]).subtract(img.select([4]))).divide(img.select([2]).add(img.select([4])));
         img = img.updateMask(ndwi_revise.gt(0));
  
  return img;
}

// Using the Landsat-8 image collection and a long time range
// 2014-01-01 to 2019-10-30 in this case
// to find the best pixels 

var landsat = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR');
landsat = landsat.map(mask);

var ls = landsat.filter(ee.Filter.date(ee.Date.fromYMD(2014,1,1),ee.Date.fromYMD(2019,10,30)));

// create mean and standard deviation images
var mean = ls.reduce(ee.Reducer.mean());
var stdev = ls.reduce(ee.Reducer.stdDev());

// display RGB image
Map.addLayer(mean.select([3,2,1]), {min: 0, max: 2000});
// var table = ee.FeatureCollection("users/dknapp4/restoration_coral_points_3857");
// Map.addLayer(table,{color:'FF0000'},"CoralRestoration")


// Export the data to Google Drive 

// Export.image.toDrive({image:mean.select([1,2,3]),
//                       description:'Landsat8',
//                       folder:'GEE_Landsat8_Mosaic',
//                       fileNamePrefix:'mean_Landsat8',
//                       region:geometry,
//                       crs: 'EPSG:3857',
//                       maxPixels: 10000000000,
//                       scale:30})
//Export.image.toDrive({image:stdev.select([1,2,3]),
//                       description:'Landsat8',
//                       folder:'GEE_Landsat8_Mosaic',
//                       fileNamePrefix:'stdev_Landsat8',
//                       region:geometry,
//                       crs: 'EPSG:3857',
//                       maxPixels: 10000000000,
//                       scale: 30});
//                       

