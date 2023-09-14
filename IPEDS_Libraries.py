import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

DATABASE_URL = "postgresql://postgres:Salinas(v)@localhost:5432/public_data_2021"
engine = create_engine(DATABASE_URL)

def load_data():
    query = "SELECT * FROM ipeds_libraries"
    return pd.read_sql(query, engine)

df = load_data()
st.title("IPEDS Libraries Demo")
st.text("""
        Welcome to the IPEDS Library Demo. This page hosts several interactive graphs that 
        can be used to explore data about academic libraries in the United States that are 
        reported to IPEDS. The first graph is a scatter plot. The x axis represents the 
        in-state cost of the institution. The y axis represents whichever variable is 
        selected in the Theme & Question drop down menu. There are also drop down menus 
        for Filters, which narrow the dataset according to institutional characteristics, 
        as well as Sliders, which allow for filtering along two continuous variables: cost 
        and enrollment. Theme and Question includes many IPEDS variables, including data on 
        students, institutional characteristics and library metrics. By selecting a theme, 
        you will be able to view the associated IPEDS variables. Selecting one of these 
        will change the y axis.""")
        

graph_types = ['Scatter', 'Bar']

# Initialize the state variables at the start of the app
if 'init' not in st.session_state:
    st.session_state.init = True
    for gtype in graph_types:
        st.session_state[f"filtered_df_{gtype}"] = df

def get_filtered_df(df, institution_names, sectors_of_institution, carnegie_classification, state_abbrs, bea_regions, years, percent_admitted, total_price, selected_question):
    # Filtering logic for all plots
    return df[
        (df['institution name_x'].isin(institution_names) | ('All' in institution_names)) &
        (df['Sector of institution'].isin(sectors_of_institution) | ('All' in sectors_of_institution)) &
        (df['Carnegie Classification 2021: Basic'].isin(carnegie_classification) | ('All' in carnegie_classification)) &
        (df['State abbreviation'].isin(state_abbrs) | ('All' in state_abbrs)) &
        (df['Bureau of Economic Analysis (BEA) regions'].isin(bea_regions) | ('All' in bea_regions)) &
        (df['year_x'].isin(years) | ('All' in years)) &
        (df['Percent admitted - total'] <= percent_admitted) &
        (df['Total price for in-state students living on campus 2021-22'] <= total_price) &
        (df['Question'] == selected_question)
    ]

def filter_and_plot(graph_type, df, institution_name_options, sector_of_institution_options, carnegie_classification_options, state_abbr_options, bea_regions_options, year_options):
    # Setting up expanders horizontally
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filters_expander = st.expander("Filters")
        with filters_expander:
            institution_names = st.multiselect('Select Institution Name', institution_name_options, default='All', key=f"institution_names_{graph_type}")
            sectors_of_institution = st.multiselect('Select Sector of Institution', sector_of_institution_options, default='All', key=f"sectors_{graph_type}")
            carnegie_classification = st.multiselect('Select Carnegie Classification 2021', carnegie_classification_options, default='All', key=f"carnegie_classification_{graph_type}")
            state_abbrs = st.multiselect('Select State Abbreviation', state_abbr_options, default='All', key=f"state_{graph_type}")
            bea_regions = st.multiselect('Select BEA Regions', bea_regions_options, default='All', key=f"regions_{graph_type}")
            years = st.multiselect('Select Year', year_options, default='All', key=f"year_{graph_type}")

    with col2:
        sliders_expander = st.expander("Sliders")
        with sliders_expander:
            percent_admitted = st.slider('Select Max Percent Admitted - total', min_value=0, max_value=100, value=100, key=f"admitted_{graph_type}")
            total_price = st.slider('Select Max Total price for in-state students living on campus 2021-22', min_value=0, max_value=100000, value=50000, key=f"price_{graph_type}")

    with col3:
        theme_expander = st.expander("Theme & Question")
        with theme_expander:
            selected_theme = st.selectbox("Select Theme", df['Theme'].unique().tolist(), key=f"theme_{graph_type}")
            available_questions = df[df['Theme'] == selected_theme]['Question'].unique().tolist()
            selected_question = st.selectbox("Select Question", available_questions, key=f"question_{graph_type}")

    # Filtering Data and creating a copy
    filtered_df = get_filtered_df(df, institution_names, sectors_of_institution, carnegie_classification, state_abbrs, bea_regions, years, percent_admitted, total_price, selected_question)
    
    filters = [institution_names, sectors_of_institution, carnegie_classification, state_abbrs, bea_regions, years, percent_admitted, total_price, selected_question]
    session_keys = [f"{graph_type}_{f}" for f in ['institution_names', 'sectors_of_institution', 'carnegie_classification', 'state_abbrs', 'bea_regions', 'years', 'admitted', 'price', 'question']]
    
    if st.session_state.init or any([st.session_state.get(k, None) != cur for k, cur in zip(session_keys, filters)]):
        # Mark the initialization as completed
        st.session_state.init = False

        # Save the current state of filters
        for k, cur in zip(session_keys, filters):
            st.session_state[k] = cur

        # Check if 'Answer' column is numerical and sort it
        filtered_df['Answer'] = pd.to_numeric(filtered_df['Answer'], errors='ignore')
        if pd.api.types.is_numeric_dtype(filtered_df['Answer']):
            filtered_df = filtered_df.sort_values(by='Answer', ascending=False)

        st.session_state[f"filtered_df_{graph_type}"] = filtered_df

    else:
        # If no changes in filters, use the session state cached filtered_df
        filtered_df = st.session_state[f"filtered_df_{graph_type}"]
    # Plotting
    def plot_scatter(df, selected_question):
        fig = px.scatter(df, 
                    x='Total price for in-state students living on campus 2021-22', 
                    y='Answer',
                    hover_name='institution name_x',
                    hover_data=None,
                    size='Total price for in-state students living on campus 2021-22',
                    opacity=.6,
                    color_discrete_sequence=px.colors.sequential.Viridis)
        fig.add_scatter(x=filtered_df['Total price for in-state students living on campus 2021-22'],
                        y=filtered_df['Answer'],
                        mode="markers",
                        marker=dict(color='white', size=filtered_df['Total price for in-state students living on campus 2021-22']*0.8, opacity=1),
                        hoverinfo='skip')
        fig.update_traces(marker=dict(symbol='circle-open', 
                             line=dict(color=fig.data[0]['marker']['color'], width=2)))
        fig.update_layout(yaxis_title=selected_question, height=600, width=800)
        return fig

    def plot_bar(df, selected_question):
        fig = px.bar(df.sort_values(by='Answer', ascending=False), 
                     x='institution name_x',
                     y='Answer',
                     labels={'institution name_x':'Institution', 'Answer':'Answer Value'},
                     height = 600,
                     width = 800,
                     color_discrete_sequence=px.colors.sequential.Viridis
                     )
        fig.update_layout(yaxis_title=selected_question)
        
        # Define data for ascending and descending sorted figures
        data_asc = px.bar(df.sort_values(by='Answer', ascending=True), 
                          x='institution name_x',
                          y='Answer',
                          labels={'institution name_x':'Institution', 'Answer':'Answer Value'},
                          height = 600,
                          width = 800,
                          color_discrete_sequence=px.colors.sequential.Viridis).data
    
        data_desc = px.bar(df.sort_values(by='Answer', ascending=False), 
                           x='institution name_x',
                           y='Answer',
                           labels={'institution name_x':'Institution', 'Answer':'Answer Value'},
                           height = 600,
                           width = 800,
                           color_discrete_sequence=px.colors.sequential.Viridis).data
    
        
        return fig


    

    if graph_type == 'Scatter':
        return plot_scatter(filtered_df, selected_question)
    elif graph_type == 'Bar':
        return plot_bar(filtered_df, selected_question)
    
available_columns = df.columns.tolist()
institution_name_options = ['All'] + list(df['institution name_x'].unique())
sector_of_institution_options = ['All'] + list(df['Sector of institution'].unique())
carnegie_classification_options = ['All'] + list(df['Carnegie Classification 2021: Basic'].unique())
state_abbr_options = ['All'] + list(df['State abbreviation'].unique())
bea_regions_options = ['All'] + list(df['Bureau of Economic Analysis (BEA) regions'].unique())
year_options = ['All'] + list(df['year_x'].unique())

for gtype in graph_types:
    fig = filter_and_plot(gtype, df, institution_name_options, sector_of_institution_options, carnegie_classification_options, state_abbr_options, bea_regions_options, year_options)
    st.plotly_chart(fig)
    if gtype == 'Scatter':
        st.write("""
        ## Exploring IPEDS Data Further
        If we want to look at the data in a different way, we can filter and explore universities using this bar graph, which shows institutions in the x axis and the selection for Question in the y axis. Lets imagine we want to understand how much of a library's budget is spent on personnel. We can select the expenses theme and then salaries and wages as a percentage of total expenditures. Now we are able to see an ordered list of institutions according to labor costs for librarians.
        """)