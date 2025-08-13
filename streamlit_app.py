# streamlit_app.py — SniS version (dynamic SmoothieFroot + fixed INSERT)
import streamlit as st
import requests
from urllib.parse import quote
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

# --- SmoothieFroot nutrition (dynamic on first selected fruit) ---
if ingredients_list:
    first_fruit = ingredients_list[0]
    st.subheader(f"🍉 Nutrition info for {first_fruit}")

    @st.cache_data(show_spinner=False, ttl=600)
    def fetch_smoothiefroot(name: str):
        # URL-encode (handles spaces/special chars)
        slug = quote(name.lower())
        url = f"https://my.smoothiefroot.com/api/fruit/{slug}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

    try:
        data = fetch_smoothiefroot(first_fruit)
        # Show parsed JSON as a nice table
        st.dataframe(data=data, use_container_width=True)
    except Exception as e:
        st.error(f"Could not retrieve nutrition info: {e}")

# --- Submit order ---
if st.button("Submit Order"):
    if not name_on_order:
        st.warning("Please enter a name for the smoothie.")
    elif not ingredients_list:
        st.warning("Please choose at least one ingredient.")
    else:
        ingredients_string = ", ".join(ingredients_list)
        try:
            # Explicit column list so other columns use table defaults
            sql = f"""
                INSERT INTO smoothies.public.orders (INGREDIENTS, NAME_ON_ORDER)
                VALUES ('{_sql_quote(ingredients_string)}', '{_sql_quote(name_on_order)}')
            """
            session.sql(sql).collect()
            st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
            # st.rerun()  # uncomment to clear selections after submit
        except Exception as e:
            st.error(f"Order failed: {e}")


