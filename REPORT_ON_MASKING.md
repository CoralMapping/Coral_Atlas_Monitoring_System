# Post-Mosaic Cloud Masking for the Allen Coral Atlas

In order to avoid including clouds and cloud shadows into the image data 
for the monitoring system, it was deemed necessary to do some post-mosaic
cloud masking of  the analytic mosaics from Planet.  In order to accomplish
this goal, an algorithm with 2 major steps was designed and implemented.

The first step is to generate a  clean Landsat-8 mosaic that is relatively 
free of clouds and cloud shadows.  This mosaic can be from a very long time 
span in order to ensure that it contains the most cloud- and show-free data.  
This is accomplished in Google Earth Engine (GEE) whereby the collected of 
Landsat imagery from 2014 to 2019 is used the collect cloud free imagery.  
The stack of cloud free images then has its mean and  standard deviation 
calculated for each pixel.  The purpose of these layers is to serve as a comparison 
to the Planet imagery to make sure that the Planet image is not too anomalous. 
The code landsat8_cloud_free_mosaic.js is included in the repo as an example of 
the way that the cloud free mosaic should be created in GEE.  Perhaps it can be 
implemented to create a Planet quad-sized result and exported into the data pipeline.
A threshold is set in the standard deviation image to remove pixels that fall 
outside of the mean +/- the standard deviation threshold.  Pixels falling 
outside of the threshold are masked.

In order to remove areas along the edges of these masked areas, we include 
a 5x5 pixel disk/circle morphological operator to mask along the edges of 
the newly masked pixels to remove any residual cloud or shadow in these areas.  

With these two main operations, a new surface reflectance image is  
written with a “_masked.tif” included to indicate that it is a masked version 
of the original quad from Planet.  If such an image exists for a quad, it should
be used in the subsequent bottom reflectance processing.

The cloud and shadow masking code has been used on a set of data for the Great
Barrier Reef (GBR) to support Ji-Wei’s turbidity mapping.  He has reported 
good performance of the algorithm for his application.
