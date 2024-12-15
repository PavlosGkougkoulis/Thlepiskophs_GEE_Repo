//RUN THIS CODE IN GOOGLE EARTH ENGINE


// Οριοθέτηση περιοχής μελέτης (Volos)
var volos = ee.Geometry.Rectangle([22.9, 39.3, 23.2, 39.5]);

// Φόρτωση δεδομένων Sentinel-2 πριν και μετά την καταιγίδα
var before = ee.ImageCollection('COPERNICUS/S2')
              .filterDate('2023-08-01', '2023-08-31')
              .filterBounds(volos)
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10));

var after = ee.ImageCollection('COPERNICUS/S2')
             .filterDate('2023-09-15', '2023-10-15')
             .filterBounds(volos)
             .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10));

// Cloud masking function using the QA60 band (cloud mask)
var cloudMask = function(image) {
  var qa60 = image.select('QA60'); // QA60 cloud mask band
  var cloudMask = qa60.bitwiseAnd(1 << 10).eq(0); // Mask out cloudy pixels
  return image.updateMask(cloudMask); // Apply the mask to the image
};

// Apply the cloud mask to both before and after images
before = before.map(cloudMask);
after = after.map(cloudMask);

// Δημιουργία συνθέσεων RGB για οπτικοποίηση
var beforeRGB = before.median().select(['B4', 'B3', 'B2']);
var afterRGB = after.median().select(['B4', 'B3', 'B2']);

// Υπολογισμός NDWI
var calcNDWI = function(image) {
  return image.normalizedDifference(['B3', 'B8']).rename('NDWI');
};

var beforeNDWI = before.map(calcNDWI).median();
var afterNDWI = after.map(calcNDWI).median();

// Υπολογισμός MNDWI
var calcMNDWI = function(image) {
  return image.normalizedDifference(['B3', 'B11']).rename('MNDWI');
};

var beforeMNDWI = before.map(calcMNDWI).median();
var afterMNDWI = after.map(calcMNDWI).median();

// Υπολογισμός NDVI
var calcNDVI = function(image) {
  return image.normalizedDifference(['B8', 'B4']).rename('NDVI');
};

var beforeNDVI = before.map(calcNDVI).median();
var afterNDVI = after.map(calcNDVI).median();

// Calculate min and max NDVI for the entire area and time range
var combinedNDVI = before.map(calcNDVI).merge(after.map(calcNDVI));
var minNDVI = combinedNDVI.reduce(ee.Reducer.min()).select('NDVI_min');
var maxNDVI = combinedNDVI.reduce(ee.Reducer.max()).select('NDVI_max');

// Function to calculate VCI with consistent min and max NDVI
var calcVCI = function(ndviImage) {
  return ndviImage.subtract(minNDVI)
                  .divide(maxNDVI.subtract(minNDVI))
                  .multiply(100)
                  .rename('VCI');
};

// Calculate VCI for before and after
var beforeVCI = calcVCI(beforeNDVI);
var afterVCI = calcVCI(afterNDVI);

// Change in VCI
var changeVCI = afterVCI.subtract(beforeVCI).rename('Change_VCI');

// Δείκτης πλημμύρας χρησιμοποιώντας SAR δεδομένα (Sentinel-1)
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
          .filterBounds(volos)
          .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
          .filter(ee.Filter.eq('instrumentMode', 'IW'));

var beforeSAR = s1.filterDate('2023-08-01', '2023-08-31').median().select('VV');
var afterSAR = s1.filterDate('2023-09-15', '2023-10-15').median().select('VV');

// Υπολογισμός πλημμυρισμένων περιοχών (κατώφλι VV)
var floodedBefore = beforeSAR.lt(-18).rename('Flooded');
var floodedAfter = afterSAR.lt(-18).rename('Flooded');

// Οπτικοποίηση
Map.centerObject(volos, 12);

// Προσθήκη στο χάρτη (RGB)
Map.addLayer(beforeRGB, {min: 0, max: 3000}, 'Before RGB');
Map.addLayer(afterRGB, {min: 0, max: 3000}, 'After RGB');

// Προσθήκη στο χάρτη (NDWI)
Map.addLayer(beforeNDWI.updateMask(beforeNDWI), {min: 0, max: 1, palette: ['blue', 'white']}, 'Before NDWI');
Map.addLayer(afterNDWI.updateMask(afterNDWI), {min: 0, max: 1, palette: ['blue', 'white']}, 'After NDWI');

// Προσθήκη στο χάρτη (MNDWI)
Map.addLayer(beforeMNDWI.updateMask(beforeMNDWI), {min: 0, max: 1, palette: ['blue', 'cyan', 'white']}, 'Before MNDWI');
Map.addLayer(afterMNDWI.updateMask(afterMNDWI), {min: 0, max: 1, palette: ['blue', 'cyan', 'white']}, 'After MNDWI');

// Προσθήκη στο χάρτη (NDVI)
Map.addLayer(beforeNDVI.updateMask(beforeNDVI), {min: 0, max: 1, palette: ['brown', 'green']}, 'Before NDVI');
Map.addLayer(afterNDVI.updateMask(afterNDVI), {min: 0, max: 1, palette: ['brown', 'green']}, 'After NDVI');

// Προσθήκη στο χάρτη (VCI)
Map.addLayer(beforeVCI.updateMask(beforeVCI), {min: 0, max: 100, palette: ['red', 'yellow', 'green']}, 'Before VCI');
Map.addLayer(afterVCI.updateMask(afterVCI), {min: 0, max: 100, palette: ['red', 'yellow', 'green']}, 'After VCI');

// Προσθήκη στο χάρτη (Πλημμυρισμένες περιοχές)
Map.addLayer(floodedBefore.updateMask(floodedBefore), {palette: ['red']}, 'Flooded Areas Before');
Map.addLayer(floodedAfter.updateMask(floodedAfter), {palette: ['blue']}, 'Flooded Areas After');

// Υπολογισμός αλλαγών
var changeNDWI = afterNDWI.subtract(beforeNDWI).rename('Change_NDWI');
var changeMNDWI = afterMNDWI.subtract(beforeMNDWI).rename('Change_MNDWI');
var changeNDVI = afterNDVI.subtract(beforeNDVI).rename('Change_NDVI');


var changeNDVI_min = changeNDVI.reduceRegion({
  reducer: ee.Reducer.min(),
  geometry: volos,
  scale: 30,
  maxPixels: 1e8
}).get('Change_NDVI');

var changeNDVI_max = changeNDVI.reduceRegion({
  reducer: ee.Reducer.max(),
  geometry: volos,
  scale: 30,
  maxPixels: 1e8
}).get('Change_NDVI');

print('Change NDVI min value:', changeNDVI_min);
print('Change NDVI max value:', changeNDVI_max);



// Προσθήκη αλλαγών στο χάρτη
Map.addLayer(changeNDWI.updateMask(changeNDWI), {min: -0.5, max: 0.5, palette: ['red', 'white', 'blue']}, 'Change NDWI');
Map.addLayer(changeMNDWI.updateMask(changeMNDWI), {min: -0.5, max: 0.5, palette: ['red', 'white', 'blue']}, 'Change MNDWI');
Map.addLayer(changeNDVI.updateMask(changeNDVI), {min: -0.6, max: 0.3, palette: ['red', 'white', 'green']}, 'Change NDVI');
Map.addLayer(changeVCI.updateMask(changeVCI), {min: -20, max: 20, palette: ['red', 'white', 'green']}, 'Change VCI');
