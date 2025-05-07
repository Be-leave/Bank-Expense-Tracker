import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os




st.set_page_config(page_title ="Bank", page_icon="\u0024",layout="wide")

category_file = "categories.json"

if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": [],
    }

if os.path.exists(category_file):
    with open(category_file,"r") as f:
        st.session_state.categories = json.load(f)

def save_categories():
    with open(category_file,"w") as f:
        json.dump(st.session_state.categories, f)


def categorize_transactions(df):
    df["Category"] = "Uncategorized"

    for category, keywords in st.session_state.categories.items():
        if category == "uncategorized" or not keywords:
            continue


        lowered_keywords = [keyword.lower().strip() for keyword in keywords]
        for idx, row in df.iterrows():
            description = row["Description"].lower().strip()
            if any(keyword in description for keyword in lowered_keywords):
                df.at[idx, "Category"] = category

    return df


def load_transactions(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]

        # Clean the Amount column - remove $ and () symbols
        df["Amount"] = df["Amount"].str.replace("$", "").str.replace(",", "")
        df["Amount"] = df["Amount"].apply(lambda x: -float(x.strip("()")) if "(" in x else float(x))

        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y")
        return df
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None


def bank():
    st.title("Simple Finance Dashboard")
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

    if uploaded_file is not None:
        df = load_transactions(uploaded_file)

        if df is not None:
            if 'transactions_df' not in st.session_state:
                st.session_state.transactions_df = df

            df = categorize_transactions(st.session_state.transactions_df)
            # Separate expenses (negative amounts) and income (positive amounts)
            expenses_df = df[df["Amount"] < 0].copy()
            expenses_df["Amount"] = expenses_df["Amount"].abs()  # Convert to positive for display
            income_df = df[df["Amount"] > 0].copy()

            tab1, tab2 = st.tabs(["Expenses", "Income"])

            with tab1:
                # Category management section remains the same
                col1, col2 = st.columns(2)
                with col1:
                    new_category = st.text_input("New Category Name")
                    add_button = st.button("Add New Category")

                    if add_button and new_category:
                        if new_category not in st.session_state.categories:
                            st.session_state.categories[new_category] = []
                            save_categories()
                            st.rerun()

                with col2:
                    if st.session_state.categories:
                        selected_category = st.selectbox("Select Category", list(st.session_state.categories.keys()))
                        new_keyword = st.text_input("Add keyword for category")
                        if st.button("Add Keyword") and new_keyword:
                            if new_keyword not in st.session_state.categories[selected_category]:
                                st.session_state.categories[selected_category].append(new_keyword)
                                save_categories()
                                st.rerun()

                # Transaction editing section
                st.subheader("Edit Transaction Categories")

                edited_df = st.data_editor(
                    expenses_df,
                    column_config={
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys()),
                            required=True,
                        ),
                        "Amount": st.column_config.NumberColumn(
                            "Amount",
                            format="$%.2f",
                        )
                    },
                    hide_index=True,
                )

                # Update the main DataFrame with any category changes
                if 'transactions_df' in st.session_state:
                    for idx, row in edited_df.iterrows():
                        st.session_state.transactions_df.loc[idx, 'Category'] = row['Category']

                # Display the pie chart with updated categories
                if not edited_df.empty:
                    fig = px.pie(edited_df, values='Amount', names='Category',
                                 title='Expenses by Category')
                    st.plotly_chart(fig)

                    # Calculate and display total spending
                    total_spending = edited_df['Amount'].sum()
                    st.metric("Total Spending", f"${total_spending:,.2f}")


bank()






