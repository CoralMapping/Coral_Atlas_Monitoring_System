# Coral_Atlas_Monitoring_System
This is a repo of the current state of the Coral Monitoring system, based largely on the Hawaii data from 20190429 through currently.
This is based on the persistent deviation concept which is being used for Hawaii.  The main idea is that a baseline period is selected in which no bleaching has occurred (for Hawaii, that is the week of April 29 through July of 2019).  For each weekly image during the baseline period, we record the maximum bottom reflectance for each pixel.  For each week during the period of possible bleaching, we compare the new week's image to that baseline maximum.  Each pixel is incremented by 1 if its bottom reflectance is above the baseline maximum.  We also record the magnitude (i.e., bottom reflectance) of that brighter pixel.  These images of the number of times above the baseline maximum form the basis on which the possibility of coral bleaching occurrs.

We are also experimenting with variations on this idea.  For example, instead of hte baseline maximum, we are also developing a probability image that a pixel is significantly above the mean baseline brightness or not.  This should help us develop ways to "dial in" or adjust the sensitivity from location to location.

There are hundreds of codes that we have dewveloped to explore, experiment, and gather statistics on the data, but to keep this repo simple and clean, I am only including those codes that are closest to being operational.

The first step in the processing is taking the surface reflectance (SR) tiles from Planet and converting them to bottom reflectance (Rb).

# depth_rb_noauto_hawaii.py
This is the code that creates the bottom reflectance (Rb) from Surface Reflectance (SR).  The SR data are in the tiles received from Planet each week.  The name of the file is a holdover from when we calculated both depth and Rb.  "Noauto" means that it does not automatically calculcated the Chl-a value.  That values is set as a constant of 0.4 until some improvement on it's estimation can be made.

Here is an example of how this code is run from Linux command line.
  depth_rb_noauto_hawaii.py L15-0131E-1144N.tif L15-0131E-1144N_br.tif 0.4
  
where: L15-0131E-1144N.tif is an input surface reflectance tile from Planet.
       L15-0131E-1144N_rb.tif is the output bottom reflectance image.  
       0.4 is the value of the Chl-a concentration of the water.  It is usually set to this constant value.

# rb_hawaii.py
This file contains code that is imported into depth_rb_noauto_hawaii.py.

# constant_values.csv
This is a text file with data needed for accounting for the water column in rb_hawaii.py

# tiles_ascdesc.txt
This is a text file listing the tile ID and whether the better tile is from the ascending or descending data.  This can be used to select one or the other tile, instead of processing both.

--------------------------------

# difference_coral_pv.py
This is the code that is the basis of creating the persistent deviation results.  It assumes that the weekly data from Planet are in a directory structure in which the tiles (4096 pixels by 4096 lines) are in a directory of the given week.  The weekly data from Planet start and end on Monday.  So, for example, the string '20190429_to_20190506' goes Monday to Monday.  They represent Planet images that have been compiled from Sunday to Sunday.

The code has a number of directories and other things hard-coded in the file, but they can be reworked as needed.  For example, there is a parameter for whether the tile is from the Ascending or Descending images.  This was done to identify which directory to get the tile from.  I have included a list (tiles_ascdesc.txt) that indicates if the better tile is from ascending or descneding data.

=======================================

# The following pieces of code are experiemntal in nature and are constantly being tweeked for different purposes.
# difference_bayes.py
This code is similar to difference_coral_pv.py, but is based on a Bayesian probability of a pixel being significantly different from the baseline.  There are other variants of this probabilistic approach, but this is the initial result.

# make_zscore_image.py
This is a code which creates a image of teh zscore for each pixel based on a baseline distribution or statistics of some other aggregation time period.

# make_zscore_image2.py
This is a variation on the previous code which has an arguement to only process up to a certain date.
