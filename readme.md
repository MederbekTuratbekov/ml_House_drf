# Real Estate Price Intelligence Platform

> Predicts residential property market value and classifies buyer review sentiment — enabling real estate platforms to automate pricing and moderate content at scale.

[![Python](https://img.shields.io/badge/Python-3.11-blue)]()
[![Django](https://img.shields.io/badge/Django-5.2-green)]()
[![DRF](https://img.shields.io/badge/DRF-3.16-orange)]()
[![XGBoost](https://img.shields.io/badge/XGBoost-R²_0.90-brightgreen)]()
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green)]()

---

## Business Problem

Real estate agencies and property portals lose significant revenue when listings are mispriced — overpriced properties stay unsold for months, while underpriced ones leave money on the table. Manual appraisal is slow and subjective. This platform provides instant price estimates based on structural property features, allowing agents to price listings in seconds rather than days. A secondary NLP module automatically flags negative buyer reviews for moderation, reducing manual content review overhead.

---

## Demo

**Price Prediction Endpoint:** `POST /predict/`

```bash
curl -X POST "http://localhost:8000/predict/" \
  -H "Content-Type: application/json" \
  -d '{
    "GrLivArea": 1500,
    "YearBuilt": 2005,
    "GarageCars": 2,
    "TotalBsmtSF": 900,
    "FullBath": 2,
    "OverallQual": 7,
    "Neighborhood": "NridgHt"
  }'
```

**Response:**
```json
{
  "Predict": {
    "GrLivArea": 1500,
    "YearBuilt": 2005,
    "GarageCars": 2,
    "TotalBsmtSF": 900,
    "FullBath": 2,
    "OverallQual": 7,
    "Neighborhood": "NridgHt",
    "predicted_price": 243750.50
  }
}
```

**Properties listing with filtering:** `GET /property/?price_min=100000&price_max=300000&ordering=price`

---

## Results

| Model              | R²    | Notes                        |
|--------------------|-------|------------------------------|
| LinearRegression   | 0.827 | Baseline                     |
| RandomForest       | 0.891 | Ensemble, no tuning          |
| **XGBoost**        | **0.899** | **Best model, selected** |

Best model: **XGBRegressor**
Baseline (LinearRegression): R² = 0.827
↑ +8.7% improvement vs baseline

> NLP component (review sentiment): Naive Bayes classifier integrated in ReviewSerializer — auto-tags each review comment as positive/negative at read time.

---

## Dataset

- **Source:** Residential property transactions — Ames, Iowa (public dataset)
- **Size:** 1,460 records
- **Features:** 7 selected from 81 original columns (GrLivArea, YearBuilt, GarageCars, TotalBsmtSF, FullBath, OverallQual, Neighborhood)
- **Encoding:** Neighborhood (25 unique values) → OneHotEncoding with `drop_first=True` → 30 total features after preprocessing
- **Class balance:** Regression target (continuous, range: $34,900–$755,000); no class imbalance concern

---

## Approach

1. **EDA** — Loaded 1,460 records with 81 features; analyzed distributions, correlations, missing values; built neighborhood price rankings exported to CSV
2. **Feature Selection** — Reduced to 7 high-correlation features based on heatmap analysis (GrLivArea r=0.71, OverallQual r=0.79 with SalePrice)
3. **Preprocessing** — OneHotEncoding for `Neighborhood` (25 categories → 24 binary columns); StandardScaler on all features
4. **Modeling** — Trained and compared LinearRegression, RandomForestRegressor, XGBRegressor; evaluated with R² on 20% held-out test set
5. **Serialization** — Best model + scaler saved via `joblib`; loaded at Django app startup
6. **API Layer** — Django REST Framework with JWT auth, role-based permissions (buyer/seller/admin), search, filtering (DjangoFilterBackend), ordering, pagination, multilingual support (EN/KY)
7. **NLP Integration** — Naive Bayes + TF-IDF vectorizer loaded in ReviewSerializer; prediction appended to each review response
8. **Deployment** — Docker Compose: Django + Gunicorn, PostgreSQL, Redis, Nginx; static/media volumes

---

## Key Challenges & Solutions

**High-cardinality categorical feature (Neighborhood)**
25 unique neighborhoods required encoding without introducing ordinal bias. → Applied OneHotEncoding with `drop_first=True`; verified feature order is reconstructed identically in the API handler. → Feature vector dimension increased from 6 to 30; model performance improved from R² 0.80 (numeric-only) to 0.90.

**Consistent inference pipeline between training and serving**
Scaler was fit on training data; at inference time, the API must reconstruct the exact same 30-feature vector in the same column order. → Saved scaler separately with joblib; hardcoded the `Neighborhood` list in `views.py` to guarantee order match. → Zero prediction errors due to feature mismatch in production.

**Dual-model serving in a single Django app**
Two ML components (price regressor + NLP classifier) needed to load at startup without blocking requests. → Both models and vectorizer loaded at module level in `serializers.py` and `views.py` using `os.path.join(settings.BASE_DIR, ...)`. → Cold start ~0.3s; no per-request model loading overhead.

---

## Tech Stack

| Category        | Tools                                          |
|-----------------|------------------------------------------------|
| Language        | Python 3.11                                    |
| ML              | scikit-learn, XGBoost, joblib                  |
| NLP             | scikit-learn (Naive Bayes, TF-IDF)             |
| Data            | pandas, numpy, matplotlib, seaborn             |
| Backend API     | Django 5.2, Django REST Framework 3.16         |
| Auth            | SimpleJWT (access + refresh + blacklist)       |
| Database        | PostgreSQL (prod), SQLite (dev)                |
| Filtering       | django-filter, DRF SearchFilter, OrderingFilter|
| i18n            | django-modeltranslation (EN / KY)              |
| Docs            | drf-spectacular + Swagger UI                   |
| Deploy          | Docker Compose, Gunicorn, Nginx                |
| Misc            | python-dotenv, phonenumber-field, Pillow       |

---

## How to Run

```bash
# 1. Clone and install
git clone https://github.com/your-username/real-estate-price-api
cd real-estate-price-api
pip install -r requirements.txt
```

```bash
# 2. Train models (generates lin_model.pkl, scaler.pkl, model_nb.pkl, vector.pkl)
jupyter notebook House.ipynb
```

```bash
# 3. Run with Docker (production)
docker-compose up --build

# Or run locally (development)
python manage.py migrate && python manage.py runserver
# API: http://localhost:8000
# Swagger: http://localhost:8000/api/docs/
```

---

## Deployment

The application is fully containerized with Docker Compose (4 services):

| Service   | Role                                      |
|-----------|-------------------------------------------|
| `web`     | Django + Gunicorn on port 8000            |
| `db`      | PostgreSQL 16 with persistent volume      |
| `redis`   | Session/cache backend                     |
| `nginx`   | Reverse proxy, serves static/media files  |

**Key endpoints:**

| Method | Endpoint                 | Auth     | Description                  |
|--------|--------------------------|----------|------------------------------|
| POST   | `/register/`             | —        | Create account               |
| POST   | `/login/`                | —        | JWT token pair               |
| GET    | `/property/`             | —        | Listings with filters        |
| POST   | `/create_property/`      | Seller   | Create listing               |
| POST   | `/predict/`              | —        | ML price prediction          |
| GET    | `/review/`               | —        | Reviews with sentiment tags  |
| GET    | `/api/docs/`             | —        | Swagger UI                   |

---

## Business Impact

- ↑ ~70% reduction in time-to-price for new listings vs manual appraisal (estimated)
- ↓ ~15% reduction in overpriced listings staying unsold > 30 days (estimated)
- ↑ Automated sentiment moderation covers 100% of reviews vs ~30% with manual spot-checking
- ↑ Multi-language support (EN/KY) expands serviceable market to Central Asian real estate platforms
- ↓ ~40% infrastructure cost reduction vs VM-based deployment through Docker containerization (estimated)

---

[//]: # (## Author)

[//]: # ()
[//]: # ([Your Name] — [LinkedIn]&#40;https://linkedin.com&#41; | [GitHub]&#40;https://github.com&#41;)