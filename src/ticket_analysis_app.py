import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

def load_data(uploaded_file):
    """Load and preprocess the Excel file."""
    df = pd.read_excel(uploaded_file, header=2)  # Assuming header starts at row 3
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Extract month from Week Closed (format: YYYYWW)
    def get_month_from_week(week_str):
        try:
            year = int(str(week_str)[:4])
            week = int(str(week_str)[4:])
            # Convert week number to date (assuming Monday as the start of the week)
            date = datetime.strptime(f'{year}-W{week:02d}-1', '%Y-W%W-%w')
            return date.month
        except ValueError:
            return None
    
    # Apply the conversion to the Week Closed column
    df['Month'] = df['Week Closed'].astype(str).apply(get_month_from_week)
    
    return df

def is_bu_ticket(group_name):
    """Helper function to determine if a ticket is BU based on group name."""
    bu_groups = ['ZD - BU Routing', 'BU Routing']
    return any(group in str(group_name) for group in bu_groups)

def analyze_tickets(df, selected_products, selected_week=None, selected_month=None):
    """Analyze ticket distribution between CS and BU."""
    # Filter by products
    filtered_df = df[df['Product'].isin(selected_products)]
    
    # Apply week filter if selected
    if selected_week:
        filtered_df = filtered_df[filtered_df['Week Closed'].astype(str) == str(selected_week)]
    
    # Apply month filter if selected
    if selected_month:
        filtered_df = filtered_df[filtered_df['Month'] == selected_month]
    
    # Calculate CS vs BU distribution based on ZD Group Name
    bu_tickets = filtered_df[filtered_df['ZD Group Name'].apply(is_bu_ticket)].shape[0]
    cs_tickets = filtered_df[~filtered_df['ZD Group Name'].apply(is_bu_ticket)].shape[0]
    
    # Calculate total and percentages
    total_tickets = cs_tickets + bu_tickets
    cs_percentage = (cs_tickets / total_tickets * 100) if total_tickets > 0 else 0
    bu_percentage = (bu_tickets / total_tickets * 100) if total_tickets > 0 else 0
    
    # Add a new column to identify ticket type
    filtered_df['Ticket Type'] = filtered_df['ZD Group Name'].apply(
        lambda x: 'BU' if is_bu_ticket(x) else 'CS'
    )
    
    return {
        'CS Tickets': cs_tickets,
        'BU Tickets': bu_tickets,
        'Total Tickets': total_tickets,
        'CS Percentage': cs_percentage,
        'BU Percentage': bu_percentage,
        'filtered_data': filtered_df
    }

def main():
    st.title("Ticket Analysis Dashboard")
    
    # File upload
    uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx'])
    
    if uploaded_file is not None:
        # Load data
        df = load_data(uploaded_file)
        
        # Sidebar filters
        st.sidebar.header("Filters")
        
        # Product filter - changed to multiselect
        products = sorted(df['Product'].unique())
        selected_products = st.sidebar.multiselect(
            "Select Products",
            products,
            default=[products[0]] if products else []  # Select first product by default
        )
        
        # Only proceed if at least one product is selected
        if not selected_products:
            st.warning("Please select at least one product to analyze.")
            return
            
        # Week filter
        weeks = sorted(df['Week Closed'].unique())
        selected_week = st.sidebar.selectbox("Select Week (Optional)", ['All'] + list(weeks))
        selected_week = None if selected_week == 'All' else selected_week
        
        # Month filter
        months = sorted(df['Month'].unique())
        selected_month = st.sidebar.selectbox("Select Month (Optional)", ['All'] + list(months))
        selected_month = None if selected_month == 'All' else selected_month
        
        # Ticket Classification filter
        ticket_types = ['All', 'CS', 'BU']
        selected_ticket_type = st.sidebar.selectbox("Select Ticket Classification", ticket_types)
        
        # Analyze data with multiple products
        results = analyze_tickets(df, selected_products, selected_week, selected_month)
        
        # Apply Ticket Classification filter
        if selected_ticket_type != 'All':
            results['filtered_data'] = results['filtered_data'][results['filtered_data']['Ticket Type'] == selected_ticket_type]
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tickets", results['Total Tickets'])
        col2.metric("CS Tickets", f"{results['CS Tickets']} ({results['CS Percentage']:.1f}%)")
        col3.metric("BU Tickets", f"{results['BU Tickets']} ({results['BU Percentage']:.1f}%)")
        
        # Display pie chart
        st.subheader("Ticket Distribution")
        fig_pie = px.pie(
            values=[results['CS Tickets'], results['BU Tickets']],
            names=['CS', 'BU'],
            title=f"CS vs BU Distribution for {', '.join(selected_products)}",
            color_discrete_sequence=['#00CC96', '#EF553B']
        )
        st.plotly_chart(fig_pie)
        
        # Display trend over time with product breakdown
        if results['filtered_data'].shape[0] > 0:
            st.subheader("Ticket Distribution Over Time")
            time_series = results['filtered_data'].groupby(['Week Closed', 'Product', 'Ticket Type']).size().reset_index(name='Count')
            fig_line = px.line(
                time_series,
                x='Week Closed',
                y='Count',
                color='Product',
                line_dash='Ticket Type',  # Use different line styles for CS vs BU
                title=f"Ticket Distribution Trend by Product",
                color_discrete_sequence=px.colors.qualitative.Set3  # More colors for multiple products
            )
            st.plotly_chart(fig_line)
        
        # Display filtered data
        st.subheader("Filtered Data")
        st.dataframe(results['filtered_data'])
        
        # Download filtered data
        csv = results['filtered_data'].to_csv(index=False)
        st.download_button(
            label="Download Filtered Data",
            data=csv,
            file_name=f"ticket_analysis_{', '.join(selected_products)}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main() 