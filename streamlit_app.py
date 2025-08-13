# streamlit_app.py — SniS version
import streamlit as st
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie!")
st.write("Choose the fruits you want in your custom Smoothie!")

# --- Connect to Snowflake (expects [connections.snowflake] in Secrets) ---
try:
    cnx = st.connection("snowflake")   # name must be "snowflake" in Secrets
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

# --- Submit ---
if st.button("Submit Order"):
    if not name_on_order:
        st.warning("Please enter a name for the smoothie.")
    elif not ingredients_list:
        st.warning("Please choose at least one ingredient.")
    else:
        ingredients_string = ", ".join(ingredients_list)

        try:
            # Insert only the columns we provide; the rest use table defaults
            orders_tbl = session.table("smoothies.public.orders")
            orders_tbl.insert(
                values=[(ingredients_string, name_on_order)],
                columns=["INGREDIENTS", "NAME_ON_ORDER"],
            )

            st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
            # st.rerun()  # uncomment to clear selections after submit
        except Exception as e:
            st.error(f"Order failed: {e}")

