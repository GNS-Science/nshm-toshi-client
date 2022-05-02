#upload_rupture_sets.py

import os
from pathlib import Path
from pathlib import PurePath
from nshm_toshi_client.toshi_file import ToshiFile
from nshm_toshi_client.toshi_task_file import ToshiTaskFile

##Production
API_URL = "https://i7gz6msaa2.execute-api.ap-southeast-2.amazonaws.com/test/graphql" #TEST
S3_URL = "https://nzshm22-toshi-api-test.s3.amazonaws.com/"
API_KEY = os.getenv("TOSHI_API_KEY")

def upload_ruptset(filename):
    file_id, post_url = file_api.create_file(PurePath(filename))
    file_api.upload_content(post_url, PurePath(filename))
    task_file_api.create_task_file(task_id, file_id, 'WRITE')

# def get_file_mappings():

#     return {
#         "nz_demo5_crustal_10km_direct_cmlRake360_jumpP0.001_slipP0.05incr_cff0.75IntsPos_comb2Paths_cffFavP0.01_cffFavRatioN2P0.5_sectFractGrow0.05.zip": "R2VuZXJhbFRhc2s6Mg==",
#         "nz_demo5_crustal_adapt5_10km_sMax1_direct_cmlRake360_jumpP0.001_slipP0.05incr_cff0.75IntsPos_comb2Paths_cffFavP0.01_cffFavRatioN2P0.5_bilateral_sectFractGrow0.05.zip": "",
#         "nz_demo5_crustal_adapt5_10km_sMax1_direct_cmlRake360_jumpP0.001_slipP0.05incr_cff0.75IntsPos_comb2Paths_cffFavP0.01_cffFavRatioN2P0.5_sectFractGrow0.05.zip": "",
#     }


def build_task_meta():
    for depth in ["CFM", "30km"]:
        for connection_strategy in ["DistCutoffClosestSect", "AdaptiveDistCutoffClosestSect"]:
            for rupture_growing_strategy in ["Unilateral", "Bilateral"]:
                yield (depth, connection_strategy, rupture_growing_strategy)

meta = [
    ('CFM', 'DistCutoffClosestSect', 'Unilateral'),
    ('CFM', 'AdaptiveDistCutoffClosestSect', 'Unilateral'),
    ('CFM', 'AdaptiveDistCutoffClosestSect', 'Bilateral'),
    ('30km', 'DistCutoffClosestSect', 'Unilateral'),
    ('30km', 'AdaptiveDistCutoffClosestSect', 'Unilateral'),
    ('30km', 'AdaptiveDistCutoffClosestSect', 'Bilateral')
]

if __name__ == "__main__":

    print("upload files to toshi prod")


    headers={"x-api-key":API_KEY}
    file_api = ToshiFile(API_URL, S3_URL, None, with_schema_validation=True, headers=headers)
    task_file_api = ToshiTaskFile(API_URL, None, with_schema_validation=True, headers=headers)

    files = [f for f in os.listdir(os.getcwd()) if ( f.endswith('.zip') and f.startswith('nz_'))]
    files.sort(key=os.path.getmtime)

    for filename in files:
        #os.path.getmtime(filename)
        print(filename)

        # task_id = get_file_mappings()[filename]
        # print('done')
    for m in meta:
        print(m)

    for i in zip(meta, files):
        print(i)

'''
## Direct  Unilateral 30KM SLOW
nz_demo5_crustal_DEPTH30__10km_direct_cmlRake360_jumpP0.001_slipP0.05incr_cff0.75IntsPos_comb2Paths_cffFavP0.01_cffFavRatioN2P0.5_sectFractGrow0.05.zip

## Adaptive Unilateral 30KM
nz_demo5_crustal_DEPTH30__adapt5_10km_sMax1_direct_cmlRake360_jumpP0.001_slipP0.05incr_cff0.75IntsPos_comb2Paths_cffFavP0.01_cffFavRatioN2P0.5_sectFractGrow0.05.zip
Built 63,759 ruptures in 386.98 secs = 6.45 mins. Total rate: 165 rups/s

## Adaptive Bilateral 30KM
'''

'''
+ splays 1, 100km
New largest rup has 150 subsections with 14 jumps and 1 splays.
    117,422 total unique passing ruptures found, longest has 150 subsections.   Clusters: 426 running (8114 futures), 15 completed, 528 total.  Rate: 219 rups/s (698 rups/s over last 25s)
    125,000 total unique passing ruptures found, longest has 150 subsections.   Clusters: 465 running (8934 futures), 15 completed, 528 total.  Rate: 223 rups/s (308 rups/s over last 25s)
    150,000 total unique passing ruptures found, longest has 153 subsections.   Clusters: 510 running (9973 futures), 18 completed, 528 total.  Rate: 222 rups/s (218 rups/s over last 1.9m)
    175,000 total unique passing ruptures found, longest has 161 subsections.   Clusters: 509 running (10022 futures), 19 completed, 528 total.     Rate: 224 rups/s (232 rups/s over last 1.8m)
    200,000 total unique passing ruptures found, longest has 161 subsections.   Clusters: 509 running (10076 futures), 19 completed, 528 total.     Rate: 226 rups/s (242 rups/s over last 1.7m)
    225,000 total unique passing ruptures found, longest has 162 subsections.   Clusters: 509 running (10114 futures), 19 completed, 528 total.     Rate: 228 rups/s (250 rups/s over last 1.7m)
    250,000 total unique passing ruptures found, longest has 172 subsections.   Clusters: 509 running (10145 futures), 19 completed, 528 total.     Rate: 229 rups/s (238 rups/s over last 1.7m)
    275,000 total unique passing ruptures found, longest has 172 subsections.   Clusters: 509 running (10355 futures), 19 completed, 528 total.     Rate: 237 rups/s (374 rups/s over last 1.1m)
    300,000 total unique passing ruptures found, longest has 172 subsections.   Clusters: 509 running (10382 futures), 19 completed, 528 total.     Rate: 237 rups/s (230 rups/s over last 1.8m)
    325,000 total unique passing ruptures found, longest has 172 subsections.   Clusters: 509 running (10390 futures), 19 completed, 528 total.     Rate: 117 rups/s (17 rups/s over last 25.2m)
    350,000 total unique passing ruptures found, longest has 172 subsections.   Clusters: 509 running (10409 futures), 19 completed, 528 total.     Rate: 61 rups/s (8.4 rups/s over last 49.9m)
    375,000 total unique passing ruptures found, longest has 173 subsections.   Clusters: 509 running (10420 futures), 19 completed, 528 total.     Rate: 37 rups/s (5.9 rups/s over last 1.2h)
    400,000 total unique passing ruptures found, longest has 177 subsections.   Clusters: 509 running (10428 futures), 19 completed, 528 total.     Rate: 26 rups/s (4.9 rups/s over last 1.4h)
    425,000 total unique passing ruptures found, longest has 177 subsections.   Clusters: 509 running (10450 futures), 19 completed, 528 total.     Rate: 12 rups/s (1.2 rups/s over last 5.9h)

'''