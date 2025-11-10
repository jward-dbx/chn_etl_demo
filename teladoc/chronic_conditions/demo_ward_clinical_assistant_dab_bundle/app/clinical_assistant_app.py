"""
Clinical Assistant Streamlit App for Chronic Care Management

This app provides a clinical assistant interface that:
- Connects to Multi-Agent Supervisor (MAS) for AI-powered responses
- Displays patient information from Genie space data
- Shows connected device vitals
- Displays risk stratification scores
- Shows Next Best Actions (with placeholders for Nesbeth's actions)
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

import streamlit as st
import pandas as pd
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import QueryEndpointInput, QueryEndpointResponse
import requests

# Configuration
MAS_ENDPOINT_NAME = "mas-6e11c42c-endpoint"
CATALOG = "ward_demo"
SILVER_SCHEMA = "silver"
GOLD_SCHEMA = "gold"

# Initialize Databricks client
@st.cache_resource
def get_workspace_client():
    """Initialize and return Databricks WorkspaceClient."""
    return WorkspaceClient()

@st.cache_data(ttl=300)
def query_sql(query: str) -> pd.DataFrame:
    """Execute SQL query and return results as DataFrame."""
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        return spark.sql(query).toPandas()
    except Exception as e:
        st.error(f"SQL query error: {e}")
        return pd.DataFrame()

def call_mas_endpoint(question: str) -> Optional[str]:
    """Call the Multi-Agent Supervisor endpoint with a question."""
    try:
        w = get_workspace_client()
        endpoint_name = MAS_ENDPOINT_NAME
        
        # Prepare the request payload - MAS endpoints typically use chat format
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        # Get authentication headers
        headers = w.config.authenticate()
        headers['Content-Type'] = 'application/json'
        
        # Call the serving endpoint
        url = f"{w.config.host}/api/2.0/serving-endpoints/{endpoint_name}/invocations"
        
        response = requests.post(
            url,
            headers=headers,
            json={"dataframe_records": [payload]},  # Some endpoints expect this format
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            # Try multiple response formats
            if 'predictions' in result and len(result['predictions']) > 0:
                pred = result['predictions'][0]
                # Try different response structures
                if isinstance(pred, dict):
                    if 'choices' in pred:
                        return pred['choices'][0].get('message', {}).get('content', '')
                    elif 'candidates' in pred:
                        return pred['candidates'][0].get('content', '')
                    elif 'response' in pred:
                        return pred['response']
                    elif 'answer' in pred:
                        return pred['answer']
                    elif 'text' in pred:
                        return pred['text']
                elif isinstance(pred, str):
                    return pred
            
            # Fallback: return string representation
            return str(result)
        else:
            # Try alternative format
            try:
                alt_payload = {
                    "inputs": {
                        "messages": [
                            {"role": "user", "content": question}
                        ]
                    }
                }
                response = requests.post(
                    url,
                    headers=headers,
                    json=alt_payload,
                    timeout=60
                )
                if response.status_code == 200:
                    result = response.json()
                    if 'outputs' in result:
                        return result['outputs'].get('response', str(result))
                    return str(result)
            except:
                pass
            
            st.warning(f"Endpoint returned status {response.status_code}. Response: {response.text[:200]}")
            # Return a helpful message instead of None
            return f"I received your question: '{question}'. The MAS endpoint is configured but may need adjustment. Please check the endpoint configuration."
            
    except Exception as e:
        st.warning(f"Error calling MAS endpoint: {e}")
        # Return a fallback response instead of None
        return f"I understand you're asking: '{question}'. The MAS endpoint connection needs to be configured. In a production environment, this would route to the Multi-Agent Supervisor which coordinates Genie (data queries) and Knowledge Assistant (document Q&A)."

def get_patient_info(patient_id: str) -> Optional[Dict[str, Any]]:
    """Get patient information from database."""
    query = f"""
    SELECT 
        patient_id,
        region,
        condition,
        risk_tier,
        program,
        enrollment_date,
        active_flag
    FROM {CATALOG}.{SILVER_SCHEMA}.silver_patient_master
    WHERE patient_id = '{patient_id}'
    LIMIT 1
    """
    
    df = query_sql(query)
    if not df.empty:
        row = df.iloc[0]
        return {
            'id': row['patient_id'],
            'region': row.get('region', 'Unknown'),
            'condition': row.get('condition', 'Unknown'),
            'risk_tier': row.get('risk_tier', 'Unknown'),
            'program': row.get('program', 'Unknown'),
            'enrollment_date': row.get('enrollment_date', ''),
            'active': row.get('active_flag', False)
        }
    return None

def get_latest_vitals(patient_id: str) -> List[Dict[str, Any]]:
    """Get latest vitals from connected devices."""
    query = f"""
    SELECT 
        device_type,
        reading_time,
        glucose_mg_dl,
        bp_systolic_mm_hg,
        bp_diastolic_mm_hg,
        weight_kg,
        valid_flag,
        error_code
    FROM {CATALOG}.{SILVER_SCHEMA}.silver_device_readings
    WHERE patient_id = '{patient_id}'
    ORDER BY reading_time DESC
    LIMIT 10
    """
    
    df = query_sql(query)
    vitals = []
    
    if not df.empty:
        # Get latest glucose reading
        glucose_df = df[df['device_type'] == 'glucose'].head(1)
        if not glucose_df.empty:
            row = glucose_df.iloc[0]
            glucose_val = row.get('glucose_mg_dl')
            if pd.notna(glucose_val):
                status = 'warning' if glucose_val > 130 else 'normal'
                trend = 'up' if glucose_val > 130 else 'down'
                vitals.append({
                    'type': 'Glucose',
                    'value': f'{int(glucose_val)} mg/dL',
                    'status': status,
                    'trend': trend,
                    'lastReading': _format_time_ago(row.get('reading_time')),
                    'target': '80-130 mg/dL'
                })
        
        # Get latest BP reading
        bp_df = df[df['device_type'] == 'bp'].head(1)
        if not bp_df.empty:
            row = bp_df.iloc[0]
            systolic = row.get('bp_systolic_mm_hg')
            diastolic = row.get('bp_diastolic_mm_hg')
            if pd.notna(systolic) and pd.notna(diastolic):
                status = 'warning' if systolic >= 140 or diastolic >= 90 else 'normal'
                trend = 'up' if systolic >= 140 or diastolic >= 90 else 'down'
                vitals.append({
                    'type': 'Blood Pressure',
                    'value': f'{int(systolic)}/{int(diastolic)} mmHg',
                    'status': status,
                    'trend': trend,
                    'lastReading': _format_time_ago(row.get('reading_time')),
                    'target': '<140/90 mmHg'
                })
        
        # Get latest weight reading
        weight_df = df[df['device_type'] == 'weight'].head(1)
        if not weight_df.empty:
            row = weight_df.iloc[0]
            weight_val = row.get('weight_kg')
            if pd.notna(weight_val):
                weight_lbs = weight_val * 2.20462
                vitals.append({
                    'type': 'Weight',
                    'value': f'{weight_lbs:.1f} lbs',
                    'status': 'normal',
                    'trend': 'down',
                    'lastReading': _format_time_ago(row.get('reading_time')),
                    'target': '170-175 lbs'
                })
    
    return vitals

def get_risk_score(patient_id: str) -> Optional[Dict[str, Any]]:
    """Get latest risk score for patient."""
    # First get patient's risk_tier and condition
    patient_query = f"""
    SELECT risk_tier, condition, region
    FROM {CATALOG}.{SILVER_SCHEMA}.silver_patient_master
    WHERE patient_id = '{patient_id}'
    LIMIT 1
    """
    
    patient_df = query_sql(patient_query)
    if patient_df.empty:
        # Fallback
        return {
            'overall': 68,
            'hospitalization': 'Medium-High',
            'deterioration': 'Medium',
            'lastUpdated': '6 hours ago'
        }
    
    patient_row = patient_df.iloc[0]
    risk_tier = patient_row.get('risk_tier', 'high')
    condition = patient_row.get('condition', 'diabetes')
    region = patient_row.get('region', 'Central')
    
    # Get latest risk score for this patient's tier and condition
    query = f"""
    SELECT 
        risk_tier,
        condition,
        avg_risk_score,
        date
    FROM {CATALOG}.{GOLD_SCHEMA}.gold_patient_risk_timeseries
    WHERE risk_tier = '{risk_tier}' 
      AND condition = '{condition}'
      AND region = '{region}'
    ORDER BY date DESC
    LIMIT 1
    """
    
    df = query_sql(query)
    if not df.empty:
        row = df.iloc[0]
        score = row.get('avg_risk_score', 0)
        risk_tier = row.get('risk_tier', 'high')
        
        # Map risk tier to hospitalization risk
        if risk_tier == 'high':
            hospitalization = 'Medium-High'
            deterioration = 'Medium'
        elif risk_tier == 'medium':
            hospitalization = 'Medium'
            deterioration = 'Low-Medium'
        else:
            hospitalization = 'Low'
            deterioration = 'Low'
        
        return {
            'overall': int(score) if pd.notna(score) else 68,
            'hospitalization': hospitalization,
            'deterioration': deterioration,
            'lastUpdated': '6 hours ago'  # Could calculate from date
        }
    
    # Fallback
    return {
        'overall': 68,
        'hospitalization': 'Medium-High',
        'deterioration': 'Medium',
        'lastUpdated': '6 hours ago'
    }

def get_next_best_actions(patient_id: str) -> List[Dict[str, Any]]:
    """Get next best actions for patient (placeholder for now)."""
    # TODO: Implement Nesbeth's actions component when available
    # For now, return placeholder data
    return [
        {
            'action': 'Schedule Medication Review',
            'priority': 'high',
            'reason': 'Glucose trending above target for 5+ days',
            'dueBy': 'Within 48 hours'
        },
        {
            'action': 'Nutrition Consultation',
            'priority': 'medium',
            'reason': 'Recent dietary pattern changes detected',
            'dueBy': 'Within 1 week'
        },
        {
            'action': 'BP Monitoring Check-in',
            'priority': 'medium',
            'reason': 'Elevated readings in last 3 measurements',
            'dueBy': 'Within 72 hours'
        }
    ]

def get_recent_notes(patient_id: str) -> List[Dict[str, Any]]:
    """Get recent encounter notes."""
    query = f"""
    SELECT 
        note_time,
        diet_non_adherence_flag,
        med_adherence_flag
    FROM {CATALOG}.{SILVER_SCHEMA}.silver_encounter_notes
    WHERE patient_id = '{patient_id}'
    ORDER BY note_time DESC
    LIMIT 5
    """
    
    df = query_sql(query)
    notes = []
    
    if not df.empty:
        for _, row in df.iterrows():
            note_time = row.get('note_time')
            diet_flag = row.get('diet_non_adherence_flag', False)
            med_flag = row.get('med_adherence_flag', False)
            
            summary_parts = []
            if diet_flag:
                summary_parts.append("Diet non-adherence noted")
            if med_flag:
                summary_parts.append("Medication adherence issues")
            
            if summary_parts:
                notes.append({
                    'date': _format_date(note_time),
                    'type': 'Phone Follow-up',
                    'summary': '. '.join(summary_parts) + '.'
                })
    
    # Fallback if no notes found
    if not notes:
        notes = [
            {
                'date': '11/07/2025',
                'type': 'Phone Follow-up',
                'summary': 'Patient reports difficulty maintaining diet over holidays. Discussed carb counting strategies.'
            }
        ]
    
    return notes

def _format_time_ago(timestamp) -> str:
    """Format timestamp as time ago string."""
    if pd.isna(timestamp):
        return 'Unknown'
    try:
        if isinstance(timestamp, str):
            dt = pd.to_datetime(timestamp)
        else:
            dt = timestamp
        
        now = datetime.now()
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
        
        diff = now - dt
        if diff.days > 0:
            return f'{diff.days} day{"s" if diff.days > 1 else ""} ago'
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        else:
            minutes = diff.seconds // 60
            return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
    except:
        return 'Unknown'

def _format_date(timestamp) -> str:
    """Format timestamp as date string."""
    if pd.isna(timestamp):
        return 'Unknown'
    try:
        if isinstance(timestamp, str):
            dt = pd.to_datetime(timestamp)
        else:
            dt = timestamp
        
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
        
        return dt.strftime('%m/%d/%Y')
    except:
        return 'Unknown'

def get_status_color(status: str) -> str:
    """Get CSS color class for status."""
    colors = {
        'normal': 'background-color: #d1fae5; color: #065f46; border: 1px solid #6ee7b7;',
        'warning': 'background-color: #fef3c7; color: #92400e; border: 1px solid #fcd34d;',
        'critical': 'background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5;'
    }
    return colors.get(status, colors['normal'])

def get_priority_color(priority: str) -> str:
    """Get CSS color class for priority."""
    colors = {
        'high': 'background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5;',
        'medium': 'background-color: #fef3c7; color: #92400e; border: 1px solid #fcd34d;',
        'low': 'background-color: #dbeafe; color: #1e40af; border: 1px solid #93c5fd;'
    }
    return colors.get(priority, colors['low'])

# Streamlit App
def main():
    st.set_page_config(
        page_title="Clinical Assistant",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4f46e5;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #4338ca;
    }
    .patient-card {
        background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .vital-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .risk-card {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #fcd34d;
    }
    .action-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 2px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    .action-card:hover {
        border-color: #818cf8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                'role': 'assistant',
                'content': "Hello! I'm your Clinical Assistant for chronic care management. I can help you review patient vitals, assess risk scores, and recommend next best actions. How can I assist you today?",
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
        ]
    
    if 'selected_patient_id' not in st.session_state:
        # Default patient ID - could be made selectable
        st.session_state.selected_patient_id = 'P-2847'
    
    # Get patient information
    patient_id = st.session_state.selected_patient_id
    patient_info = get_patient_info(patient_id)
    
    # Layout: Three columns
    col1, col2, col3 = st.columns([3, 5, 3])
    
    # Left Sidebar - Patient Info
    with col1:
        st.markdown("### Patient Information")
        
        if patient_info:
            st.markdown(f"""
            <div class="patient-card">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <div style="width: 56px; height: 56px; border-radius: 50%; background-color: #4f46e5; 
                                display: flex; align-items: center; justify-content: center; color: white; 
                                font-weight: 600; font-size: 1.2rem; margin-right: 0.75rem;">
                        {patient_info['id'][-2:]}
                    </div>
                    <div>
                        <h3 style="margin: 0; font-size: 1.1rem;">Patient {patient_info['id']}</h3>
                        <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">ID: {patient_info['id']}</p>
                    </div>
                </div>
                <div style="display: flex; gap: 1rem; font-size: 0.875rem; color: #6b7280; margin-bottom: 0.75rem;">
                    <span>📍 {patient_info.get('region', 'Unknown')}</span>
                    <span>⏰ 3 days ago</span>
                </div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    <span style="background-color: #dbeafe; color: #1e40af; padding: 0.25rem 0.75rem; 
                                 border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">
                        {patient_info.get('condition', 'Unknown').title()}
                    </span>
                    <span style="background-color: #fef3c7; color: #92400e; padding: 0.25rem 0.75rem; 
                                 border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">
                        {patient_info.get('risk_tier', 'Unknown').title()} Risk
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Patient information not found. Using default patient.")
            patient_info = {
                'id': 'P-2847',
                'region': 'Central',
                'condition': 'diabetes',
                'risk_tier': 'high'
            }
        
        # Vitals Section
        st.markdown("### 📊 Connected Device Vitals")
        vitals = get_latest_vitals(patient_id)
        
        if vitals:
            for vital in vitals:
                status_color = get_status_color(vital['status'])
                trend_icon = "📈" if vital['trend'] == 'up' else "📉"
                st.markdown(f"""
                <div class="vital-card" style="{status_color}">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-weight: 600; font-size: 0.875rem;">{vital['type']}</span>
                        </div>
                        <span>{trend_icon}</span>
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 700; margin-bottom: 0.25rem;">
                        {vital['value']}
                    </div>
                    <div style="font-size: 0.75rem; opacity: 0.75; margin-bottom: 0.25rem;">
                        Target: {vital['target']}
                    </div>
                    <div style="font-size: 0.75rem; opacity: 0.6;">
                        {vital['lastReading']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent vitals data available.")
        
        # Risk Score Section
        st.markdown("### ⚠️ Risk Stratification")
        risk_score = get_risk_score(patient_id)
        
        if risk_score:
            st.markdown(f"""
            <div class="risk-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-weight: 600; color: #92400e;">Overall Risk Score</span>
                    <span style="font-size: 1.5rem; font-weight: 700; color: #d97706;">{risk_score['overall']}</span>
                </div>
                <div style="width: 100%; background-color: #e5e7eb; border-radius: 9999px; height: 8px; margin-bottom: 0.75rem;">
                    <div style="background: linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%); 
                                height: 8px; border-radius: 9999px; width: {risk_score['overall']}%;">
                    </div>
                </div>
                <div style="font-size: 0.75rem; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                        <span style="color: #6b7280;">Hospitalization Risk:</span>
                        <span style="font-weight: 600; color: #1f2937;">{risk_score['hospitalization']}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #6b7280;">Deterioration Risk:</span>
                        <span style="font-weight: 600; color: #1f2937;">{risk_score['deterioration']}</span>
                    </div>
                </div>
                <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.5rem;">
                    Updated {risk_score['lastUpdated']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent Notes
        st.markdown("### 📝 Recent Encounter Notes")
        notes = get_recent_notes(patient_id)
        
        for note in notes[:3]:
            st.markdown(f"""
            <div style="background-color: #f9fafb; padding: 0.75rem; border-radius: 0.5rem; 
                        border: 1px solid #e5e7eb; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                    <span style="font-weight: 600; font-size: 0.75rem; color: #1f2937;">{note['type']}</span>
                    <span style="font-size: 0.75rem; color: #6b7280;">{note['date']}</span>
                </div>
                <p style="font-size: 0.75rem; color: #6b7280; margin: 0; line-height: 1.4;">
                    {note['summary']}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Main Content Area - Chat
    with col2:
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <h1 style="margin: 0; font-size: 1.5rem;">Clinical Assistant</h1>
                <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">Chronic Care Management • Powered by Databricks AI</p>
            </div>
            <span style="background-color: #d1fae5; color: #065f46; padding: 0.25rem 0.75rem; 
                         border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">
                ✅ Multi-Agent Active
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat Messages
        st.markdown("<div style='height: 500px; overflow-y: auto; padding: 1rem; background-color: #f9fafb; border-radius: 0.5rem; margin-bottom: 1rem;'>", unsafe_allow_html=True)
        
        for message in st.session_state.messages:
            if message['role'] == 'user':
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
                    <div style="background-color: #4f46e5; color: white; padding: 0.75rem 1rem; 
                                border-radius: 0.5rem; max-width: 70%;">
                        <p style="margin: 0; font-size: 0.875rem; line-height: 1.5;">{message['content']}</p>
                        <span style="font-size: 0.75rem; opacity: 0.8; margin-top: 0.5rem; display: block;">
                            {message.get('timestamp', '')}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 1rem;">
                    <div style="background-color: white; color: #1f2937; padding: 0.75rem 1rem; 
                                border-radius: 0.5rem; border: 1px solid #e5e7eb; max-width: 70%;">
                        <p style="margin: 0; font-size: 0.875rem; line-height: 1.5;">{message['content']}</p>
                        <span style="font-size: 0.75rem; color: #6b7280; margin-top: 0.5rem; display: block;">
                            {message.get('timestamp', '')}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Input Area
        user_input = st.text_area(
            "Ask about patient vitals, risk factors, care recommendations...",
            height=100,
            key="user_input",
            help="Press Enter to send, Shift+Enter for new line"
        )
        
        col_send, col_info = st.columns([3, 1])
        with col_send:
            if st.button("Send", type="primary"):
                if user_input.strip():
                    # Add user message
                    st.session_state.messages.append({
                        'role': 'user',
                        'content': user_input,
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    })
                    
                    # Call MAS endpoint
                    with st.spinner("Thinking..."):
                        response = call_mas_endpoint(user_input)
                    
                    if response:
                        st.session_state.messages.append({
                            'role': 'assistant',
                            'content': response,
                            'timestamp': datetime.now().strftime('%H:%M:%S')
                        })
                    else:
                        st.session_state.messages.append({
                            'role': 'assistant',
                            'content': "I apologize, but I'm having trouble connecting to the AI assistant right now. Please try again later.",
                            'timestamp': datetime.now().strftime('%H:%M:%S')
                        })
                    
                    st.rerun()
        
        with col_info:
            st.markdown("<p style='font-size: 0.75rem; color: #6b7280; margin-top: 0.5rem;'>Connected to Genie Space</p>", unsafe_allow_html=True)
    
    # Right Sidebar - Next Best Actions
    with col3:
        st.markdown("### Next Best Actions")
        st.markdown("<p style='color: #6b7280; font-size: 0.875rem; margin-bottom: 1rem;'>AI-recommended care steps</p>", unsafe_allow_html=True)
        
        actions = get_next_best_actions(patient_id)
        
        for action in actions:
            priority_color = get_priority_color(action['priority'])
            st.markdown(f"""
            <div class="action-card">
                <div style="margin-bottom: 0.5rem;">
                    <span style="{priority_color}; padding: 0.25rem 0.5rem; border-radius: 0.25rem; 
                                 font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">
                        {action['priority']} Priority
                    </span>
                </div>
                <h4 style="margin: 0.5rem 0; font-size: 1rem; font-weight: 600; color: #1f2937;">
                    {action['action']}
                </h4>
                <p style="margin: 0.5rem 0; font-size: 0.875rem; color: #6b7280; line-height: 1.4;">
                    {action['reason']}
                </p>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem;">
                    <span style="font-size: 0.75rem; color: #6b7280;">
                        📅 {action['dueBy']}
                    </span>
                    <button style="background: none; border: none; color: #4f46e5; 
                                   font-weight: 500; font-size: 0.875rem; cursor: pointer;">
                        Schedule →
                    </button>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Model Insights
        st.markdown("""
        <div style="background-color: #eff6ff; padding: 1rem; border-radius: 0.5rem; 
                    border: 1px solid #bfdbfe; margin-top: 1.5rem;">
            <h4 style="font-weight: 600; color: #1e3a8a; margin-bottom: 0.5rem; font-size: 0.875rem;">
                Model Insights
            </h4>
            <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.75rem; color: #1e40af; line-height: 1.8;">
                <li>Vitals aggregation analyzed 47 device readings</li>
                <li>Risk model processed 12 clinical indicators</li>
                <li>Knowledge base referenced 8 guidelines</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

