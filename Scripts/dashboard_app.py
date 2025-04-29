import os
import pandas as pd
import joblib
import requests
import streamlit as st

# 1. Détermine le dossier où est ce script (Scripts/)
current_dir = os.path.dirname(__file__)  

# 2. Remonte d’un niveau pour arriver à la racine du repo (dashboard_pret_ml/)
root_dir = os.path.dirname(current_dir)

# 3. Construis le chemin vers ton fichier CSV dans Data/
data_path = os.path.join(root_dir, "Data", "application_train.csv")

headers = {
    "ML-api-key": "super-secret-API-key"
}

# 4. Charge les données
st.title("Tableau de bord d'éligibilité au prêt - Néo Banque")
data = pd.read_csv(data_path)


# Calcul de l'âge
data['AGE'] = (-data['DAYS_BIRTH'] / 365).astype(int)

#  Filtres globaux (exploration)
st.sidebar.header("Filtres de recherche")

age_min, age_max = st.sidebar.slider("Âge", int(data['AGE'].min()), int(data['AGE'].max()), (25, 60))
revenu_min, revenu_max = st.sidebar.slider("Revenu total (€)", int(data['AMT_INCOME_TOTAL'].min()), int(data['AMT_INCOME_TOTAL'].max()), (50000, 300000))

genre = st.sidebar.multiselect("Sexe", options=data['CODE_GENDER'].unique(), default=data['CODE_GENDER'].unique())
revenu_type = st.sidebar.multiselect("Type de revenu", options=data['NAME_INCOME_TYPE'].unique(), default=data['NAME_INCOME_TYPE'].unique())

#  Application des filtres
filtered_data = data[
    (data['AGE'] >= age_min) &
    (data['AGE'] <= age_max) &
    (data['AMT_INCOME_TOTAL'] >= revenu_min) &
    (data['AMT_INCOME_TOTAL'] <= revenu_max) &
    (data['CODE_GENDER'].isin(genre)) &
    (data['NAME_INCOME_TYPE'].isin(revenu_type))
]

#  Sélection du client via ID parmi ceux filtrés
client_id = st.selectbox("Sélectionner un ID client :", options=filtered_data['SK_ID_CURR'].sort_values())

# Récupération des données du client sélectionné
client_data = filtered_data[filtered_data['SK_ID_CURR'] == client_id]

#  Affichage des infos descriptives
st.subheader("Informations du client sélectionné")

descriptive_fields = {
    "CODE_GENDER": "Sexe",
    "NAME_CONTRACT_TYPE": "Type de contrat",
    "NAME_INCOME_TYPE": "Type de revenu",
    "AMT_INCOME_TOTAL": "Revenu total",
    "CNT_CHILDREN": "Nombre d'enfants",
    "NAME_EDUCATION_TYPE": "Niveau d’éducation",
    "NAME_FAMILY_STATUS": "Situation familiale",
    "NAME_HOUSING_TYPE": "Type de logement",
    "AGE": "Âge (années)",
    "AMT_CREDIT": "Montant du crédit demandé",
    "AMT_ANNUITY": "Montant des annuités",
    "OCCUPATION_TYPE": "Profession",
    "CNT_FAM_MEMBERS": "Nombre de personnes dans le foyer"
}

for col, label in descriptive_fields.items():
    st.write(f"**{label}** : {client_data.iloc[0][col]}")

# Explication du score d’éligibilité
st.subheader("Interprétation du Score d'Éligibilité")
st.write("""
Le score d'éligibilité au prêt est calculé en fonction de multiples facteurs financiers et personnels du client.
- **Score inférieur à 0.3** : Le client est considéré comme à risque.
- **Score entre 0.3 et 0.6** : Le client doit être étudié plus en détail.
- **Score entre 0.6 et 0.85** : Le client est probablement éligible pour un prêt.
- **Score supérieur à 0.85** : Le client est éligible pour un prêt avec une faible probabilité de risque.
""")


# Score d’éligibilité via API
if st.button("Évaluer l’éligibilité"):
    payload = client_data.drop(columns=["TARGET", "SK_ID_CURR"]).fillna(-999).iloc[0].to_dict()
    response = requests.post("http://localhost:8000/predict", json=payload, headers=headers)

    if response.status_code == 200:
        score = response.json()["score"]
        st.metric("Score d’éligibilité", round(score, 3))

        if score < 0.3:
            st.error("Client à risque")
        elif score < 0.6:
            st.warning("Client à étudier")
        elif score < 0.85:
            st.success("Client probablement éligible")
        else:
            st.success("Client éligible")
    else:
        st.error("Erreur lors de la requête à l’API")