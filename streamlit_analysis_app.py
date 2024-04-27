import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import plotly.express as px
import ast

class FirebaseHandler:
    def __init__(self):
        self.db = None

    

    
    # Function to initialize Firebase Admin SDK with the uploaded service account credentials
    def initialize_firebase(self, uploaded_file):
        try:
            # Check if Firebase Admin SDK is already initialized
            if not firebase_admin._apps:
                # Read the contents of the uploaded file
                file_contents = uploaded_file.getvalue().decode('utf-8')
                # Parse the file contents as a dictionary
                cred_dict = ast.literal_eval(file_contents)
                # Initialize Firebase Admin SDK with the parsed credentials dictionary
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                st.success("Firebase initialized successfully!")
            else:
                st.warning("Firebase is already initialized. Skipping initialization.")
            
            # Get a Firestore client to interact with the database
            self.db = firestore.client()
            return self.db
        except Exception as e:
            st.error(f"Error initializing Firebase: {e}")

# Function to fetch data from Firestore
def fetch_firestore_data(db, collection_name='user-activity'):
    all_data = []
    # Example: Get data from a Firestore collection
    collection_ref = db.collection('user-activity')#.document("101.44.161.71").collection("activities")
    # Query the documents in the collection
    docs = collection_ref.list_documents()
    # Extract document IDs
    document_user_ips = [doc.id for doc in docs]
    st.subheader("Loaded Data :")
    progress_bar=st.progress(0) 
    for i, doc_ip in enumerate(document_user_ips):
        collection_data = db.collection('user-activity').document(doc_ip).collection("activities").stream()
    # Query the documents in the collection
        for doc_act in collection_data:
            data = doc_act.to_dict()
            data['doc_ip'] = doc_ip
            all_data.append(data)

        progress_count = (i + 1) / len(document_user_ips)
        progress_bar.progress(progress_count)  # Update progress bar
            
    return all_data

# Data wrangling function
def data_wrangle(data_frame):
    df = data_frame
    
    df['geolocation'] = df['geolocation'].fillna('{"country_code": "none"}')  # Replace NaN values with empty strings
    df['geolocation'] = df['geolocation'].astype(str)
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
def main(df):
    st.title("Data Analysis App")

    st.write()
    if df is not None:



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



# Create an instance of FirebaseHandler
firebase_handler = FirebaseHandler()

# Streamlit Sidebar
st.sidebar.title("Upload Service Account Credentials")
uploaded_file = st.sidebar.file_uploader("Upload Service Account JSON", type="json")

# Initialize Firebase Admin SDK if credentials file is uploaded
if uploaded_file is not None:
    firebase_handler.initialize_firebase(uploaded_file=uploaded_file)

# Button to load data
if st.sidebar.button("Load Data"):

            if firebase_handler.db is not None:
                data = fetch_firestore_data(firebase_handler.db)
                if data:
                    st.write("Fetched Data:")
                    df = pd.DataFrame(data)   
                    df=data_wrangle(df)          
                    main(df)# Pass the DataFrame  to the main function

                else:
                    st.write("No data found in the collection.")


