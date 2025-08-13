# streamlit_app.py — SniS version (fixed INSERT for Snowpark)
import streamlit as st
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie!")
st.write("Choose the fruits you want in your custom Smoothie!")

# --- Connect to Snowflake (expects [connections.snowflake] in Secrets) ---
try:
    cnx = st.connection("snowflake")   # connection name in Secrets
    session = cnx.session()            # Snowpark session
except Exception:
    st.error("Snowflake connection is not configured.")
    st.caption("Add a [connections.snowflake] block in Streamlit Secrets or pass kwargs to st.connection().")
    st.stop()

# --- Inputs ---
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order or "—")

# --- Data helpers ---
@st.cache_data(ttl=300)
def get_fruit_options():
    return (
        session.table("smoothies.public.fruit_options")
        .select(col("FRUIT_NAME"))
        .sort(col("FRUIT_NAME"))
        .to_pandas()["FRUIT_NAME"]
        .tolist()
    )

fruit_options = get_fruit_options()

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_options,
    max_selections=5,
)

def _sql_quote(s: str) -> str:
    """Escape single quotes for SQL literals."""
    return s.replace("'", "''")

# --- Submit ---
if st.button("Submit Order"):
    if not name_on_order:
        st.warning("Please enter a name for the smoothie.")
    elif not ingredients_list:
        st.warning("Please choose at least one ingredient.")
    else:
        ingredients_string = ", ".join(ingredients_list)

        try:
            # Use explicit INSERT with a column list so defaults populate the others
            sql = f"""
                INSERT INTO smoothies.public.orders (INGREDIENTS, NAME_ON_ORDER)
                VALUES ('{_sql_quote(ingredients_string)}', '{_sql_quote(name_on_order)}')
            """
            session.sql(sql).collect()

            st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
            # st.rerun()  # uncomment to clear selections after submit
        except Exception as e:
            st.error(f"Order failed: {e}")
# New section to display SmoothieFroot nutrition information
import requests

st.subheader("🍉 SmoothieFroot Nutrition Info")

try:
    smoothie_url = "https://my.smoothiefroot.com/api/fruit/watermelon"
    smoothie_response = requests.get(smoothie_url)

    if smoothie_response.status_code == 200:
        data = smoothie_response.json()
        st.write(data)  # show the parsed JSON
    else:
        st.error(f"API request failed with status {smoothie_response.status_code}")

except Exception as e:
    st.error(f"Error calling SmoothieFroot API: {e}")

