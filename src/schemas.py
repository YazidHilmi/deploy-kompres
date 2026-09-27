FEATURE_COLUMNS = [
    "NDVI_mean",
    "EVI_mean",
    "SAVI_mean",
    "Bulan_sin",
    "Bulan_cos",
    "Kab_Jember",
    "Kab_Lamongan",
    "Kab_Ngawi",
    "Kab_Tuban",
    "NDVI_mean_delta1",
    "SAVI_mean_delta1",
    "NDVI_mean_lag2",
    "SAVI_mean_lag1",
    "NDVI_mean_lag1",
    "SAVI_mean_lag2",
    "NDVI_mean_roll3",
    "SAVI_mean_roll3",
    "EVI_mean_delta1",
]

SUPPORTED_REGIONS = [
    "Bojonegoro",
    "Jember",
    "Lamongan",
    "Ngawi",
    "Tuban",
]

REGION_DUMMIES = {
    "Bojonegoro": {
        "Kab_Jember": 0,
        "Kab_Lamongan": 0,
        "Kab_Ngawi": 0,
        "Kab_Tuban": 0,
    },
    "Jember": {
        "Kab_Jember": 1,
        "Kab_Lamongan": 0,
        "Kab_Ngawi": 0,
        "Kab_Tuban": 0,
    },
    "Lamongan": {
        "Kab_Jember": 0,
        "Kab_Lamongan": 1,
        "Kab_Ngawi": 0,
        "Kab_Tuban": 0,
    },
    "Ngawi": {
        "Kab_Jember": 0,
        "Kab_Lamongan": 0,
        "Kab_Ngawi": 1,
        "Kab_Tuban": 0,
    },
    "Tuban": {
        "Kab_Jember": 0,
        "Kab_Lamongan": 0,
        "Kab_Ngawi": 0,
        "Kab_Tuban": 1,
    },
}