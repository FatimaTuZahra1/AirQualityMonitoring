


# from fastapi import FastAPI, Query
# import requests, pickle, pandas as pd, numpy as np
# from datetime import datetime, timedelta

# app = FastAPI()

# # ─── Load RF regressor at startup ────────────────────────────────────────────
# with open('rf_regressor_model_mob.pkl','rb') as f:
#     MODEL_OBJ   = pickle.load(f)

# FEATURES     = MODEL_OBJ['features']
# NORM_PARAMS  = MODEL_OBJ['norm_params']
# RF_MODEL     = MODEL_OBJ['model']

# # ─── EPA AQI helpers ─────────────────────────────────────────────────────────
# def calc_aqi_us(conc, pollutant):
#     if pollutant == 'PM2.5':
#         c_lo = [0,    12.1,  35.5,  55.5, 150.5, 250.5, 350.5, 500.5]
#         c_hi = [12,   35.4,  55.4, 150.4, 250.4, 350.4, 500.4,1000.0]
#         i_lo = [0,    51,   101,   151,   201,   301,   401,   501]
#         i_hi = [50,  100,   150,   200,   300,   400,   500,   9999]
#     elif pollutant == 'PM10':
#         c_lo = [0,    55,   155,   255,   355,   425,   505,   605]
#         c_hi = [54,  154,   254,   354,   424,   504,   604,   999.0]
#         i_lo = [0,    51,   101,   151,   201,   301,   401,   501]
#         i_hi = [50,  100,   150,   200,   300,   400,   500,   9999]
#     elif pollutant == 'CO':
#         c_lo = [0,    4.5,   9.5,  12.5,  15.5,  30.5,  40.5]
#         c_hi = [4.4,  9.4,  12.4,  15.4,  30.4,  40.4,  50.4]
#         i_lo = [0,    51,   101,   151,   201,   301,   401]
#         i_hi = [50,  100,   150,   200,   300,   400,   500]
#     else:
#         return np.nan

#     c = float(conc)
#     for lo, hi, ilo, ihi in zip(c_lo, c_hi, i_lo, i_hi):
#         if lo <= c <= hi:
#             return round(((ihi-ilo)/(hi-lo))*(c-lo) + ilo, 1)
#     # above highest breakpoint
#     return round(((i_hi[-1]-i_lo[-1])/(c_hi[-1]-c_lo[-1]))*(c-c_lo[-1]) + i_lo[-1], 1)

# def categorize_aqi(aqi):
#     if pd.isna(aqi): return 'Unknown'
#     aqi = max(0.0, aqi)
#     if aqi <= 50:   return 'Good'
#     if aqi <= 100:  return 'Moderate'
#     if aqi <= 150:  return 'Unhealthy for Sensitive Groups'
#     if aqi <= 200:  return 'Unhealthy'
#     if aqi <= 300:  return 'Very Unhealthy'
#     return 'Hazardous'

# # ─── ML helper: RF regression → numeric AQI → category ──────────────────────
# def ml_predict(record):
#     df0 = pd.DataFrame([record])[FEATURES]
#     for col, p in NORM_PARAMS.items():
#         df0[col] = (df0[col] - p['mean']) / (p['max'] - p['min'])
#     raw = RF_MODEL.predict(df0)[0]
#     aqi = round(max(0.0, raw), 1)
#     return aqi, categorize_aqi(aqi)

# # ─── /latest endpoint ────────────────────────────────────────────────────────
# @app.get("/latest")
# def latest():
#     rec = requests.get(
#       "https://api.thingspeak.com/channels/2953164/feeds.json?results=1"
#     ).json()['feeds'][0]

#     data = {
#       'PM2.5':       float(rec.get('field2') or 0),
#       'PM10':        float(rec.get('field3') or 0),
#       'Temperature': float(rec.get('field4') or 0),
#       'Humidity':    float(rec.get('field5') or 0),
#       'CO':          float(rec.get('field6') or 0),
#     }

#     # EPA AQI
#     epa_vals     = [calc_aqi_us(data['PM2.5'], 'PM2.5'),
#                     calc_aqi_us(data['PM10'],  'PM10'),
#                     calc_aqi_us(data['CO'],    'CO')]
#     epa_aqi      = max(epa_vals)
#     epa_category = categorize_aqi(epa_aqi)

#     # ML AQI
#     ml_aqi, ml_cat = ml_predict(data)

#     return {
#       'timestamp':    rec.get('created_at'),
#       **data,
#       'epa_aqi':      epa_aqi,
#       'epa_category': epa_category,
#       'ml_aqi':       ml_aqi,
#       'ml_category':  ml_cat
#     }

# # ─── /feeds endpoint (multiple records) ────────────────────────────────────
# @app.get("/feeds")
# def get_all_feeds(
#     results: int = Query(100, ge=1, le=8000,
#                         description="How many ThingSpeak records to fetch")
# ):
#     feeds = requests.get(
#         f"https://api.thingspeak.com/channels/2953164/feeds.json?results={results}"
#     ).json().get('feeds', [])

#     output = []
#     for rec in feeds:
#         data = {
#           'PM2.5':       float(rec.get('field2') or 0),
#           'PM10':        float(rec.get('field3') or 0),
#           'Temperature': float(rec.get('field4') or 0),
#           'Humidity':    float(rec.get('field5') or 0),
#           'CO':          float(rec.get('field6') or 0),
#         }

#         epa_vals     = [calc_aqi_us(data['PM2.5'], 'PM2.5'),
#                         calc_aqi_us(data['PM10'],  'PM10'),
#                         calc_aqi_us(data['CO'],    'CO')]
#         epa_aqi      = max(epa_vals)
#         epa_category = categorize_aqi(epa_aqi)

#         ml_aqi, ml_cat = ml_predict(data)

#         output.append({
#           'timestamp':    rec.get('created_at'),
#           **data,
#           'epa_aqi':      epa_aqi,
#           'epa_category': epa_category,
#           'ml_aqi':       ml_aqi,
#           'ml_category':  ml_cat
#         })

#     return output

# # ─── /forecast endpoint ─────────────────────────────────────────────────────
# @app.get("/forecast")
# def forecast():
#     latest_rec = latest()[0]
#     ts = datetime.fromisoformat(latest_rec['timestamp'].replace('Z','+00:00'))
#     latest_rec['timestamp'] = (ts + timedelta(days=1)).isoformat()
#     return [latest_rec]


from fastapi import FastAPI, Query
import requests, pickle, pandas as pd
from datetime import datetime, timedelta

app = FastAPI()

# load once at startup
# ─── Load RF regressor at startup ────────────────────────────────────────────
with open('rf_regressor_model_mob.pkl','rb') as f:
# with open('linear_reg_model_mob_smote.pkl','rb') as f:
# with open('linear_reg_model_mob.pkl','rb') as f:
    MODEL_OBJ   = pickle.load(f)

FEATURES     = MODEL_OBJ['features']
NORM_PARAMS  = MODEL_OBJ['norm_params']
RF_MODEL     = MODEL_OBJ['model']

def calc_aqi_us(conc, pollutant):
    # breakpoints per EPA spec
    if pollutant == 'PM2.5':
        c_lo = [0,    12.1,  35.5,  55.5, 150.5, 250.5, 350.5, 500.5]
        c_hi = [12,   35.4,  55.4, 150.4, 250.4, 350.4, 500.4,1000.0]
        i_lo = [0,    51,   101,   151,   201,   301,   401,   501]
        i_hi = [50,  100,   150,   200,   300,   400,   500,   9999]
    elif pollutant == 'PM10':
        c_lo = [0,    55,   155,   255,   355,   425,   505,   605]
        c_hi = [54,  154,   254,   354,   424,   504,   604,   999.0]
        i_lo = [0,    51,   101,   151,   201,   301,   401,   501]
        i_hi = [50,  100,   150,   200,   300,   400,   500,   9999]
    elif pollutant == 'CO':
        c_lo = [0,    4.5,   9.5,  12.5,  15.5,  30.5,  40.5]
        c_hi = [4.4,  9.4,  12.4,  15.4,  30.4,  40.4,  50.4]
        i_lo = [0,    51,   101,   151,   201,   301,   401]
        i_hi = [50,  100,   150,   200,   300,   400,   500]
    else:
        return np.nan

    c = float(conc)
    for lo, hi, ilo, ihi in zip(c_lo, c_hi, i_lo, i_hi):
        if lo <= c <= hi:
            return round(((ihi-ilo)/(hi-lo))*(c-lo) + ilo, 1)
    # if above highest breakpoint:
    return round(((i_hi[-1]-i_lo[-1])/(c_hi[-1]-c_lo[-1]))*(c-c_lo[-1]) + i_lo[-1], 1)


def categorize_aqi(aqi):
    if pd.isna(aqi): return 'Unknown'
    aqi = max(0.0, aqi)
    if aqi <= 50:   return 'Good'
    if aqi <= 100:  return 'Moderate'
    if aqi <= 150:  return 'Unhealthy for Sensitive Groups'
    if aqi <= 200:  return 'Unhealthy'
    if aqi <= 300:  return 'Very Unhealthy'
    return 'Hazardous'

def ml_predict(record):
    df0 = pd.DataFrame([record])[FEATURES]
    for col, p in NORM_PARAMS.items():
        df0[col] = (df0[col] - p['mean']) / (p['max'] - p['min'])
    # raw = LR_MODEL.predict(df0)[0]
    raw = RF_MODEL.predict(df0)[0]

    aqi = round(max(0.0, raw),1)
    return aqi, categorize_aqi(aqi)

@app.get("/latest")
def latest():
    rec = requests.get(
      "https://api.thingspeak.com/channels/2953164/feeds.json?results=1"
    ).json()['feeds'][0]

    data = {
      'PM2.5':       float(rec['field2'] or 0),
      'PM10':        float(rec['field3'] or 0),
      'Temperature': float(rec['field4'] or 0),
      'Humidity':    float(rec['field5'] or 0),
      'CO':          float(rec['field6'] or 0),
    }

    # EPA AQI (max of individual)
    epa_vals = [
      calc_aqi_us(data['PM2.5'],'PM2.5'),
      calc_aqi_us(data['PM10'], 'PM10'),
      calc_aqi_us(data['CO'],   'CO')
    ]
    epa_aqi, epa_cat = max(epa_vals), categorize_aqi(max(epa_vals))

    # ML AQI
    ml_aqi, ml_cat = ml_predict(data)

    return {
      'timestamp':    rec['created_at'],
      **data,
      'epa_aqi':      epa_aqi,
      'epa_category': epa_cat,
      'ml_aqi':       ml_aqi,
      'ml_category':  ml_cat
    }

@app.get("/feeds")
def get_all_feeds(
    results: int = Query(100, ge=1, le=8000, description="How many ThingSpeak records to fetch")
):
    payload = requests.get(
        f"https://api.thingspeak.com/channels/2953164/feeds.json?results={results}"
    ).json().get('feeds', [])

    output = []
    for rec in payload:
        record = {
            'timestamp':    rec.get('created_at'),
            'PM2.5':        float(rec.get('field2', 0)),
            'PM10':         float(rec.get('field3', 0)),
            'Temperature':  float(rec.get('field4', 0)),
            'Humidity':     float(rec.get('field5', 0)),
            'CO':           float(rec.get('field6', 0)),
        }

        # EPA AQI per‐pollutant and overall
        epa_vals = [
            calc_aqi_us(record['PM2.5'], 'PM2.5'),
            calc_aqi_us(record['PM10'],  'PM10'),
            calc_aqi_us(record['CO'],    'CO'),
        ]
        record['epa_aqi']      = max(epa_vals)
        record['epa_category'] = categorize_aqi(record['epa_aqi'])

        # ML AQI + category
        ml, ml_cat = ml_predict(record)
        record['ml_aqi']       = ml
        record['ml_category']  = ml_cat

        output.append(record)

    return output

@app.get("/forecast")
def forecast():
    # if you want to keep /forecast, just call latest() and shift timestamp
    res = latest()
    ts  = datetime.fromisoformat(res['timestamp'].replace('Z','+00:00'))
    res['timestamp'] = (ts + timedelta(days=1)).isoformat()
    return res
# /forecast and /feeds can remain the same pattern—
# just call latest() internally or loop ml_predict() per record.


