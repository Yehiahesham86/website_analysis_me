import pandas as pd
import streamlit as st
import plotly.express as px
import ast

def data_wrangle(path):
    df = pd.read_csv(path)
    # Convert strings to dictionaries
    df['geolocation'] = df['geolocation'].apply(ast.literal_eval)

    # Extracting value associated with the key 'country_code'
    df['geolocation'] = df['geolocation'].apply(lambda x: x['country_code'] )

    # Extracting offer number from "URL"
    df['Offer_Number'] = df['url'].str.extract(r'/(\d+)/')

    df = df[df.doc_ip != "156.214.241.99"]
    # Rename 'geolocation' column to 'country'
    df.rename(columns={'geolocation': 'country'}, inplace=True)

    # Convert Unix timestamps to Pandas Timestamp objects
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    # Extract date and time components into separate columns
    df['date'] = df['timestamp'].dt.date
    df['time'] = df['timestamp'].dt.strftime('%H') # Format time to 24-hour with AM/PM
    
    df.drop(columns=['user_agent_version',"response_size","query_parameters","session_id","user_agent","user_id","request_headers"], inplace=True)

    return df 

# Create Streamlit app
def main():
    st.title("Data Analysis App")

    # Upload CSV file
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded_file is not None:
        df = data_wrangle(uploaded_file)

        # Display DataFrame info and head
        st.subheader("DataFrame Info:")
        st.write(df.info())

        st.subheader("DataFrame Head:")
        st.write(df.head())

        # Plot histograms
        st.subheader("Top 10 Offer Numbers Histogram:")
        fig_offer_numbers = px.histogram(x=df['Offer_Number'].value_counts().head(10).index.sort_values(ascending=False),
                                         y=df['Offer_Number'].value_counts().head(10).sort_values(ascending=False))
        st.plotly_chart(fig_offer_numbers)

        st.subheader("Visitors per Day:")
        fig_visitors_per_day = px.scatter(x=df['date'].value_counts().sort_index().index,
                                          y=df['date'].value_counts().sort_index(),
                                          title='Visitors per day')
        fig_visitors_per_day.update_xaxes(title_text='Day')
        fig_visitors_per_day.update_yaxes(title_text='Visitors')
        fig_visitors_per_day.update_layout(title_x=0.5)
        st.plotly_chart(fig_visitors_per_day)

        st.subheader("Visitors per Hour:")
        fig_visitors_per_hour = px.line(x=df['time'].value_counts().sort_index().index,
                                        y=df['time'].value_counts().sort_index(),
                                        title='Visitors per Hour')
        fig_visitors_per_hour.update_xaxes(title_text='Hour')
        fig_visitors_per_hour.update_yaxes(title_text='Visitors')
        fig_visitors_per_hour.update_layout(title_x=0.5)
        st.plotly_chart(fig_visitors_per_hour)

        st.subheader("Top 10 Referers:")
        fig_top_referers = px.scatter(df['referer'].value_counts().head(10))
        st.plotly_chart(fig_top_referers)

        st.subheader("User Agent Platform Histogram:")
        fig_user_agent_platform = px.histogram(df, x='user_agent_platform', color='user_agent_platform')
        st.plotly_chart(fig_user_agent_platform)

        st.subheader("User Agent Browser Histogram:")
        fig_user_agent_browser = px.histogram(df, x='user_agent_browser', color='user_agent_browser')
        st.plotly_chart(fig_user_agent_browser)

        st.subheader("Top 10 Visited Countries:")
        fig_top_countries = px.histogram(x=df['country'].value_counts().sort_values(ascending=False).head(10).index,
                                          y=df['country'].value_counts().sort_values(ascending=False).head(10),
                                          color=df['country'].value_counts().sort_values(ascending=False).head(10),
                                          title='Top 10 Visited Countries')
        st.plotly_chart(fig_top_countries)

if __name__ == '__main__':
    main()
