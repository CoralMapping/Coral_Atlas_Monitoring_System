

#0815-0819 0820-0824 0825-0829 0830-0903
#rclone copy asu_gdrive:/bleaching_data/ .
#for date in 0805-0810 0810-0814; do sbatch -n 1 --mem=10000 --wrap="gdal_translate surface_reflectance/rgbn_${date}.vrt surface_reflectance/rgbn_${date}.tif -co COMPRESS=LZW -co TILED=YES -co BIGTIFF=YES"; done


SR_FILE=$1
BR_FILE=$2
BR_FILE_COMP=$3


#python ~/bin/match_extent.py ../sentinel/depth_ll/depth.vrt ${SR_FILE} ${DEPTH_FILE}
python depth_rb_noauto.py ${SR_FILE} ${BR_FILE} 0.4
gdal_translate ${BR_FILE} ${BR_FILE_COMP} -co COMPRESS=DEFLATE -co TILED=YES
#gdaladdo ${BR_FILE_COMP} 2 4 8 16 32 64 128
