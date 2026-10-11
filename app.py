import streamlit as st

# Configuration de la page web
st.set_page_config(
    page_title="ErgoVeille",
    page_icon="🧠",
    layout="wide"
)

# Affichage du titre et de l'en-tête
st.title("🧠 ErgoVeille")
st.header("Tableau de bord de veille scientifique en ergothérapie")

st.markdown("---")

# Création de 3 colonnes pour les statistiques (vides pour l'instant)
col1, col2, col3 = st.columns(3)
col1.metric(label="📚 Articles collectés", value="0")
col2.metric(label="✨ Nouveautés cette semaine", value="0")
col3.metric(label="🏥 Sources surveillées", value="1")

st.markdown("---")
st.info("👋 Bienvenue sur ErgoVeille ! L'architecture du projet est en place et le moteur du tableau de bord est opérationnel. La prochaine étape sera de connecter le collecteur PubMed.")