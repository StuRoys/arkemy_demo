# utils/styles.py

def get_tab_css():
    """
    Returns CSS styling for tabs.
    """
    return """
    <style>
    /* Tab text size */
    .st-emotion-cache-89jlt8 p {
        font-size: 20px !important;
        font-weight: 700 !important;
    }

    /* Tab spacing */
    [data-testid="stHorizontalBlock"] [data-baseweb="tab-list"] {
        gap: 20px !important;
    }

    /* Make tabs look like buttons */
    [data-baseweb="tab"] {
        padding: 10px 20px !important;
        background-color: #f0f2f6 !important;
        border-radius: 10px !important;
        border: 1px solid #e0e0e0 !important;
        transition: all 0.3s !important;
    }

    /* Selected tab styling */
    [data-baseweb="tab"][aria-selected="true"] {
        background-color: #4e89ae !important;
        color: white !important;
        border-color: #4e89ae !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }

    /* Override any default red text or border */
    [data-baseweb="tab-highlight"] {
        background-color: transparent !important;
        display: none !important;
    }

    /* Remove any underlines from tabs */
    [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Hide the red indicator line */
    [data-baseweb="tab"] [role="tab"]::after {
        background-color: transparent !important;
        height: 0 !important;
    }

    /* Hover effects */
    [data-baseweb="tab"]:hover {
        background-color: #e6e9ef !important;
        border-color: #c0c0c0 !important;
    }

    [data-baseweb="tab"][aria-selected="true"]:hover {
        background-color: #3d7a9a !important;
        border-color: #3d7a9a !important;
    }
    </style>
    """