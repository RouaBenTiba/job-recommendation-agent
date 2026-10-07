# Modèle de données

Version texte du modèle de données (US-2.1), lisible directement sur GitHub et modifiable avec un diff.
Le document complet (MCD, dictionnaire des colonnes, contraintes, traçabilité) est dans `modele-de-donnees-US-2.1.docx`.

## Schéma relationnel

```mermaid
erDiagram
    users ||--o{ cvs : "uploads"
    users ||--o{ candidate_profiles : "has versions"
    cvs |o--o{ candidate_profiles : "source of"
    users ||--o| preferences : "defines"
    users ||--o{ searches : "launches"
    candidate_profiles |o--o{ searches : "used by"
    searches ||--o{ recommendations : "produces"
    job_offers ||--o{ recommendations : "recommended in"

    users {
        uuid id PK
        varchar email UK
        varchar password_hash
        varchar full_name
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
        timestamptz last_login_at
    }

    cvs {
        uuid id PK
        uuid user_id FK
        varchar filename
        varchar content_type
        integer file_size_bytes
        varchar storage_path
        text extracted_text
        varchar status
        text error_message
        timestamptz created_at
        timestamptz updated_at
    }

    candidate_profiles {
        uuid id PK
        uuid user_id FK
        uuid cv_id FK
        integer version
        boolean is_current
        text summary
        jsonb education
        jsonb experiences
        jsonb skills
        jsonb technologies
        jsonb interests
        text objectives
        varchar source
        varchar extraction_model
        timestamptz created_at
        timestamptz updated_at
    }

    preferences {
        uuid id PK
        uuid user_id FK
        text_array contract_types
        text_array locations
        text_array domains
        boolean remote_ok
        boolean willing_to_relocate
        timestamptz created_at
        timestamptz updated_at
    }

    job_offers {
        uuid id PK
        varchar source
        varchar external_id
        varchar title
        varchar company
        varchar location
        char country
        varchar contract_type
        text description
        jsonb required_skills
        varchar url
        timestamptz published_at
        timestamptz fetched_at
        varchar status
        char content_hash UK
        timestamptz indexed_at
        timestamptz created_at
        timestamptz updated_at
    }

    searches {
        uuid id PK
        uuid user_id FK
        uuid profile_id FK
        text objective
        jsonb filters
        varchar status
        integer iterations_count
        text error_message
        timestamptz started_at
        timestamptz completed_at
        timestamptz created_at
    }

    recommendations {
        uuid id PK
        uuid search_id FK
        uuid job_offer_id FK
        integer rank_position
        numeric score
        jsonb score_breakdown
        text explanation
        jsonb matched_skills
        jsonb missing_skills
        timestamptz created_at
    }
```

## Contraintes d'unicité

| Table | Contrainte |
|---|---|
| `users` | `UNIQUE (email)` (email normalisé en minuscules) |
| `preferences` | `UNIQUE (user_id)` |
| `candidate_profiles` | `UNIQUE (user_id, version)` ; index unique partiel sur `(user_id)` `WHERE is_current` |
| `job_offers` | `UNIQUE (source, external_id)` ; `UNIQUE (content_hash)` |
| `recommendations` | `UNIQUE (search_id, job_offer_id)` ; `UNIQUE (search_id, rank_position)` |

## Suppressions (ON DELETE)

| Clé étrangère | Règle |
|---|---|
| `cvs.user_id`, `candidate_profiles.user_id`, `preferences.user_id`, `searches.user_id` | `CASCADE` |
| `recommendations.search_id` | `CASCADE` |
| `candidate_profiles.cv_id`, `searches.profile_id` | `SET NULL` |
| `recommendations.job_offer_id` | `RESTRICT` (une offre se passe en `expired`, elle ne se supprime pas) |

## Tables prévues plus tard

- `search_steps` : trace de chaque tour de la boucle de l'agent (US-7.8, 7.9, 7.12, 7.13)
- `offer_feedback` : offres sauvegardées ou rejetées (US-6.5, extension)
