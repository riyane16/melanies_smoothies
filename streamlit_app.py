# Streamlit (SniS) – Customize Your Smoothie
import streamlit as st
from snowflake.snowpark.functions import col

st.title(":cup_with_straw: Customize Your Smoothie!")
st.write("Choose the fruits you want in your custom Smoothie!")

# --- Connect to Snowflake (SniS style) ---
# Requires a connection named "snowflake" in .streamlit/secrets.toml
cnx = st.connection("snowflake")
session = cnx.session()  # Snowpark session

# --- Inputs ---
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order or "—")

# Get fruit options and convert to a Python list
fruit_options = (
    session.table("smoothies.public.fruit_options")
    .select(col("FRUIT_NAME"))
    .sort(col("FRUIT_NAME"))
    .to_pandas()["FRUIT_NAME"]
    .tolist()
)

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
        # Store a readable string like "Apple, Mango"
        ingredients_string = ", ".join(ingredients_list)

        try:
            # Append using Snowpark (avoids manual SQL and injection issues)
            (
                session.create_dataframe(
                    [(ingredients_string, name_on_order)],
                    schema=["INGREDIENTS", "NAME_ON_ORDER"],
                )
                .write.save_as_table(
                    "smoothies.public.orders",
                    mode="append",
                )
            )
            st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
            # st.rerun()  # uncomment if you want to clear the selection after submit
        except Exception as e:
            st.error(f"Order failed: {e}")



